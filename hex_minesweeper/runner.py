"""Episode runner with explicit action, model-call, timeout, and trace limits."""

from __future__ import annotations

from dataclasses import dataclass, field
from queue import Empty, Queue
import random
from threading import Thread
import time
from typing import Any, Callable

from .game import BOARD_PRESETS, Game, IllegalAction
from .model_agent import MAX_PUBLIC_HISTORY, ModelAgent, ModelCallError, pricing_metadata
from .solver import choose_solver_action

MAX_STEPS = 80
MAX_MODEL_CALLS = 80
MODEL_TIMEOUT_SECONDS = 20


@dataclass
class EpisodeRunner:
    seed: int | str
    game: Game = field(default_factory=Game)
    max_steps: int = MAX_STEPS
    max_model_calls: int = MAX_MODEL_CALLS
    model_timeout_seconds: float = MODEL_TIMEOUT_SECONDS
    fixed_opening: tuple[int, int] | None = None
    board_size: str | None = None
    steps: int = 0
    model_calls: int = 0
    illegal_actions: int = 0
    fallback_actions: int = 0
    terminal_override: dict[str, Any] | None = None
    trace: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=lambda: {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    })
    latency_ms: list[int] = field(default_factory=list)
    estimated_cost_usd: float | None = 0.0
    model_name: str | None = None
    model_history_mode: str | None = None
    model_api_enabled: bool = False

    def __post_init__(self) -> None:
        if self.board_size is not None:
            if self.board_size not in BOARD_PRESETS:
                raise ValueError("board size must be small, medium, or large")
            self.game = Game(**BOARD_PRESETS[self.board_size])
        else:
            self.board_size = next(
                (name for name, config in BOARD_PRESETS.items()
                 if (self.game.radius, self.game.mine_count) ==
                 (config["radius"], config["mine_count"])),
                "custom",
            )
        self.game.reset(self.seed)
        if self.fixed_opening is not None:
            q, r = self.fixed_opening
            transition = self.game.step("player", {"type": "reveal", "q": q, "r": r})
            self.trace.append({
                "actor": "shared_evaluation_opening",
                "action": {"type": "reveal", "q": q, "r": r},
                "event": transition["event"],
            })

    def observe(self, player_id: str = "player") -> dict[str, Any]:
        return self.game.observe(player_id)

    def legal_actions(self, player_id: str = "player") -> list[dict[str, Any]]:
        if self.outcome()["terminal"]:
            return []
        return self.game.legal_actions(player_id)

    def outcome(self) -> dict[str, Any]:
        if self.terminal_override is not None:
            return dict(self.terminal_override)
        game_outcome = self.game.outcome()
        if not game_outcome["terminal"] and self.steps >= self.max_steps:
            return {
                "terminal": True,
                "reason": "step_limit",
                "result": "incomplete",
                "score": game_outcome["score"],
            }
        if not game_outcome["terminal"] and self.model_calls >= self.max_model_calls:
            return {
                "terminal": True,
                "reason": "model_call_limit",
                "result": "incomplete",
                "score": game_outcome["score"],
            }
        return game_outcome

    def step(self, player_id: str, action: dict[str, Any], actor: str = "human") -> dict[str, Any]:
        if self.outcome()["terminal"]:
            raise IllegalAction("episode is already terminal")
        if self.steps >= self.max_steps:
            self.terminal_override = self._limited_outcome("step_limit")
            raise IllegalAction("step limit reached")
        self.steps += 1
        return self._apply(action, actor, count_step=False)

    def baseline_step(self) -> dict[str, Any]:
        """Take one move using the same observation/action boundary as the model."""
        if self.outcome()["terminal"]:
            return self.snapshot()
        if self.steps >= self.max_steps:
            self.terminal_override = self._limited_outcome("step_limit")
            return self.snapshot()
        observation = self.observe("baseline")
        actions = self.legal_actions("baseline")
        self.steps += 1
        action = choose_solver_action(observation, actions)
        return self._apply(action, "baseline", count_step=False)

    def model_step(self, agent: ModelAgent | None = None) -> dict[str, Any]:
        """Request a move, retry one invalid selection, then safely fall back."""
        if self.outcome()["terminal"]:
            return self.snapshot()
        if self.steps >= self.max_steps:
            self.terminal_override = self._limited_outcome("step_limit")
            return self.snapshot()
        if self.model_calls >= self.max_model_calls:
            self.terminal_override = self._limited_outcome("model_call_limit")
            return self.snapshot()

        agent = agent or ModelAgent(timeout=self.model_timeout_seconds)
        observation = self.observe("model")
        actions = self.legal_actions("model")
        history_mode = getattr(agent, "history_mode", "observation_only")
        if history_mode not in ("observation_only", "bounded"):
            raise ValueError("model agent history_mode must be observation_only or bounded")
        history_limit = getattr(agent, "history_limit", MAX_PUBLIC_HISTORY)
        public_history = self._public_history(history_limit) if history_mode == "bounded" else None
        self.model_name = agent.model
        self.model_history_mode = history_mode
        rejected_action: dict[str, Any] | None = None

        for attempt in (1, 2):
            if attempt == 2 and (
                self.steps >= self.max_steps or self.model_calls >= self.max_model_calls
            ):
                return self._apply_random_fallback(
                    actions, reason="retry_limit_reached", attempts=attempt - 1
                )

            self.model_calls += 1
            self.steps += 1  # Each failed attempt consumes both episode budgets.
            started = time.monotonic()
            result_queue: Queue[tuple[str, Any]] = Queue(maxsize=1)
            rejected_for_attempt = rejected_action

            def request_decision() -> None:
                try:
                    kwargs: dict[str, Any] = {}
                    if public_history is not None:
                        kwargs["history"] = public_history
                    if rejected_for_attempt is not None and isinstance(agent, ModelAgent):
                        kwargs["rejected_action"] = rejected_for_attempt
                    decision = agent.choose_action(observation, actions, **kwargs)
                    result_queue.put(("decision", decision))
                except Exception as error:
                    result_queue.put(("error", error))

            Thread(target=request_decision, name="hex-minesweeper-model-call", daemon=True).start()
            try:
                kind, result = result_queue.get(timeout=self.model_timeout_seconds)
            except Empty:
                elapsed = int((time.monotonic() - started) * 1000)
                self.latency_ms.append(elapsed)
                self._add_usage(0, 0, None)
                detail = "Model call exceeded the {:.3g} second deadline.".format(
                    self.model_timeout_seconds
                )
                self.trace.append({
                    "actor": "model",
                    "error": detail,
                    "latency_ms": elapsed,
                    "model_call": self.model_calls,
                    "model_attempt": attempt,
                    "usage_unknown": True,
                })
                if attempt == 2 and rejected_for_attempt is not None:
                    return self._apply_random_fallback(
                        actions, reason="retry_timeout", attempts=attempt
                    )
                self.terminal_override = self._limited_outcome(
                    "model_timeout", detail=detail, actor="model"
                )
                return self.snapshot()

            if kind == "error":
                error = result
                if not isinstance(error, ModelCallError):
                    error = ModelCallError("Model call failed: " + str(error))
                elapsed = int((time.monotonic() - started) * 1000)
                self.latency_ms.append(elapsed)
                self._add_usage(
                    error.input_tokens,
                    error.output_tokens,
                    error.estimated_cost_usd,
                    error.cache_creation_input_tokens,
                    error.cache_read_input_tokens,
                )
                self.trace.append({
                    "actor": "model",
                    "error": str(error),
                    "latency_ms": elapsed,
                    "model_call": self.model_calls,
                    "model_attempt": attempt,
                    **self._model_usage_fields(error),
                })
                if attempt == 2 and rejected_for_attempt is not None:
                    return self._apply_random_fallback(
                        actions, reason="retry_error", attempts=attempt
                    )
                reason = "model_timeout" if error.timed_out else "model_error"
                self.terminal_override = self._limited_outcome(
                    reason, detail=str(error), actor="model"
                )
                return self.snapshot()

            decision = result
            elapsed = int((time.monotonic() - started) * 1000)
            self.latency_ms.append(elapsed)
            self._add_usage(
                decision.input_tokens,
                decision.output_tokens,
                decision.estimated_cost_usd,
                decision.cache_creation_input_tokens,
                decision.cache_read_input_tokens,
            )
            if not self._is_legal_model_action(decision.action, actions):
                self.illegal_actions += 1
                self.trace.append({
                    "actor": "model",
                    "action": decision.action,
                    "error": "invalid_model_action",
                    "latency_ms": elapsed,
                    "model_call": self.model_calls,
                    "model_attempt": attempt,
                    **self._model_usage_fields(decision),
                })
                if attempt == 1:
                    rejected_action = (
                        dict(decision.action)
                        if isinstance(decision.action, dict)
                        else {"invalid_action": repr(decision.action)}
                    )
                    continue
                return self._apply_random_fallback(
                    actions, reason="second_invalid_action", attempts=attempt
                )

            result = self._apply(decision.action, "model", count_step=False)
            self.trace[-1].update({
                "model_call": self.model_calls,
                "model_attempt": attempt,
                "latency_ms": elapsed,
                **self._model_usage_fields(decision),
            })
            if attempt == 2:
                self.trace[-1]["retried_after_invalid_action"] = True
            result["metrics"] = self.metrics()
            return result

        return self.snapshot()

    def _apply_random_fallback(
        self, actions: list[dict[str, Any]], reason: str, attempts: int
    ) -> dict[str, Any]:
        """Apply a seeded-random legal move so fallback runs remain reproducible."""
        if not actions:
            self.terminal_override = self._limited_outcome(
                "invalid_model_action", detail="no legal action was available for fallback",
                actor="random_fallback",
            )
            return self.snapshot()
        rng = random.Random("{}|{}|{}".format(self.seed, self.steps, self.model_calls))
        action = dict(actions[rng.randrange(len(actions))])
        self.fallback_actions += 1
        result = self._apply(action, "random_fallback", count_step=False)
        self.trace[-1].update({
            "fallback_reason": reason,
            "model_attempts": attempts,
        })
        result["metrics"] = self.metrics()
        return result

    def _apply(self, action: dict[str, Any], actor: str, count_step: bool) -> dict[str, Any]:
        del count_step
        try:
            transition = self.game.step(actor, action)
        except IllegalAction:
            self.illegal_actions += 1
            if actor == "model":
                self.terminal_override = self._limited_outcome(
                    "invalid_model_action", detail="model submitted an illegal action",
                    actor=actor,
                )
            raise
        self.trace.append({
            "actor": actor,
            "action": dict(action),
            "event": transition["event"],
            "step": self.steps,
        })
        return {
            "observation": transition["observation"],
            "legal_actions": self.legal_actions(actor),
            "outcome": self.outcome(),
            "event": transition["event"],
            "metrics": self.metrics(),
        }

    @staticmethod
    def _is_legal_model_action(action: Any, legal_actions: list[dict[str, Any]]) -> bool:
        """Require an exact action shape before Python equality checks legality."""
        if not isinstance(action, dict) or set(action) != {"type", "q", "r"}:
            return False
        if type(action["type"]) is not str or action["type"] not in ("reveal", "flag"):
            return False
        # bool is an int subclass, and 1.0 compares equal to 1 in dictionaries.
        if type(action["q"]) is not int or type(action["r"]) is not int:
            return False
        return action in legal_actions

    def _add_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        estimated_cost_usd: float | None,
        cache_creation_input_tokens: int = 0,
        cache_read_input_tokens: int = 0,
    ) -> None:
        self.usage["input_tokens"] += input_tokens
        self.usage["output_tokens"] += output_tokens
        self.usage["cache_creation_input_tokens"] += cache_creation_input_tokens
        self.usage["cache_read_input_tokens"] += cache_read_input_tokens
        if estimated_cost_usd is None:
            self.estimated_cost_usd = None
        elif self.estimated_cost_usd is not None:
            self.estimated_cost_usd += estimated_cost_usd

    @staticmethod
    def _model_usage_fields(result: Any) -> dict[str, Any]:
        return {
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "cache_creation_input_tokens": result.cache_creation_input_tokens,
            "cache_read_input_tokens": result.cache_read_input_tokens,
            "estimated_cost_usd": result.estimated_cost_usd,
        }

    def _limited_outcome(
        self, reason: str, detail: str | None = None, actor: str | None = None
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "terminal": True,
            "reason": reason,
            "result": "incomplete",
            "score": self.game.outcome()["score"],
        }
        if detail is not None:
            result["detail"] = detail
        if actor is not None:
            result["actor"] = actor
        return result

    def metrics(self) -> dict[str, Any]:
        # Count applied player moves separately from decision steps: invalid
        # model attempts consume steps but do not change the game state.
        actions = sum(
            1 for record in self.trace
            if record.get("event") is not None
            and record.get("actor") != "shared_evaluation_opening"
        )
        return {
            "actions": actions,
            "steps": self.steps,
            "model_calls": self.model_calls,
            "illegal_actions": self.illegal_actions,
            "fallback_actions": self.fallback_actions,
            "latency_ms": list(self.latency_ms),
            "input_tokens": self.usage["input_tokens"],
            "output_tokens": self.usage["output_tokens"],
            "cache_creation_input_tokens": self.usage["cache_creation_input_tokens"],
            "cache_read_input_tokens": self.usage["cache_read_input_tokens"],
            "estimated_cost_usd": self.estimated_cost_usd,
            "model": self.model_name,
            "model_history_mode": self.model_history_mode,
            "pricing": pricing_metadata(),
        }

    def _public_history(self, limit: int) -> list[dict[str, Any]]:
        """Return only recent actions/results already public to the player."""
        if isinstance(limit, bool) or not isinstance(limit, int) or not (
            1 <= limit <= MAX_PUBLIC_HISTORY
        ):
            raise ValueError("history limit must be between 1 and 8")
        history = []
        for record in self.trace:
            action = record.get("action")
            event = record.get("event") or {}
            if not isinstance(action, dict) or event.get("result") not in (
                "flagged", "unflagged", "revealed"
            ):
                continue
            history.append({
                "action": dict(action),
                "result": event["result"],
                "changed": list(event.get("changed", [])),
            })
        return history[-limit:]

    def snapshot(self) -> dict[str, Any]:
        return {
            "observation": self.observe(),
            "legal_actions": self.legal_actions(),
            "outcome": self.outcome(),
            "metrics": self.metrics(),
        }
