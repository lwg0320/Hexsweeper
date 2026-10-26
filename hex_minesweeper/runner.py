"""Episode runner with explicit action, model-call, timeout, and trace limits."""

from __future__ import annotations

from dataclasses import dataclass, field
from queue import Empty, Queue
from threading import Thread
import time
from typing import Any, Callable

from .game import Game, IllegalAction
from .model_agent import ModelAgent, ModelCallError, pricing_metadata
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
    steps: int = 0
    model_calls: int = 0
    illegal_actions: int = 0
    terminal_override: dict[str, Any] | None = None
    trace: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=lambda: {"input_tokens": 0, "output_tokens": 0})
    latency_ms: list[int] = field(default_factory=list)
    estimated_cost_usd: float | None = 0.0
    model_name: str | None = None

    def __post_init__(self) -> None:
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
        """Make one live provider call, validate its move, and apply it."""
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
        self.model_calls += 1
        self.steps += 1  # A failed model turn still consumes a step budget.
        self.model_name = agent.model
        started = time.monotonic()
        result_queue: Queue[tuple[str, Any]] = Queue(maxsize=1)

        def request_decision() -> None:
            try:
                result_queue.put(("decision", agent.choose_action(observation, actions)))
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
            self.terminal_override = self._limited_outcome(
                "model_timeout", detail=detail, actor="model"
            )
            self.trace.append({
                "actor": "model",
                "error": detail,
                "latency_ms": elapsed,
                "model_call": self.model_calls,
            })
            return self.snapshot()
        if kind == "error":
            error = result
            if not isinstance(error, ModelCallError):
                error = ModelCallError("Model call failed: " + str(error))
            elapsed = int((time.monotonic() - started) * 1000)
            self.latency_ms.append(elapsed)
            self._add_usage(error.input_tokens, error.output_tokens, error.estimated_cost_usd)
            reason = "model_timeout" if error.timed_out else "model_error"
            self.terminal_override = self._limited_outcome(
                reason, detail=str(error), actor="model"
            )
            self.trace.append({
                "actor": "model",
                "error": str(error),
                "latency_ms": elapsed,
                "model_call": self.model_calls,
            })
            return self.snapshot()

        decision = result

        elapsed = int((time.monotonic() - started) * 1000)
        self.latency_ms.append(elapsed)
        self._add_usage(
            decision.input_tokens, decision.output_tokens, decision.estimated_cost_usd
        )
        if decision.action not in actions:
            self.illegal_actions += 1
            self.terminal_override = self._limited_outcome(
                "invalid_model_action", detail="model selected an action outside legal_actions",
                actor="model",
            )
            self.trace.append({
                "actor": "model",
                "action": decision.action,
                "error": "invalid_model_action",
                "latency_ms": elapsed,
                "model_call": self.model_calls,
                "input_tokens": decision.input_tokens,
                "output_tokens": decision.output_tokens,
            })
            return self.snapshot()
        result = self._apply(decision.action, "model", count_step=False)
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

    def _add_usage(
        self, input_tokens: int, output_tokens: int, estimated_cost_usd: float | None
    ) -> None:
        self.usage["input_tokens"] += input_tokens
        self.usage["output_tokens"] += output_tokens
        if estimated_cost_usd is None:
            self.estimated_cost_usd = None
        elif self.estimated_cost_usd is not None:
            self.estimated_cost_usd += estimated_cost_usd

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
        return {
            "steps": self.steps,
            "model_calls": self.model_calls,
            "illegal_actions": self.illegal_actions,
            "latency_ms": list(self.latency_ms),
            "input_tokens": self.usage["input_tokens"],
            "output_tokens": self.usage["output_tokens"],
            "estimated_cost_usd": self.estimated_cost_usd,
            "model": self.model_name,
            "pricing": pricing_metadata(),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "observation": self.observe(),
            "legal_actions": self.legal_actions(),
            "outcome": self.outcome(),
            "metrics": self.metrics(),
        }
