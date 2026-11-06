"""Server-side OpenAI Responses API adapter with one constrained move tool."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import os
import socket
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_MODEL = "gpt-6-astra"
MAX_PUBLIC_HISTORY = 8


class ModelCallError(RuntimeError):
    def __init__(
        self, message: str, *, timed_out: bool = False, input_tokens: int = 0,
        output_tokens: int = 0, estimated_cost_usd: float | None = None
    ):
        super().__init__(message)
        self.timed_out = timed_out
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.estimated_cost_usd = estimated_cost_usd


@dataclass(frozen=True)
class Decision:
    action: dict[str, Any]
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float | None = None


class ModelAgent:
    """Ask a language model for exactly one legal game action."""

    def __init__(
        self,
        model: str | None = None,
        timeout: float = 20,
        history_mode: str = "observation_only",
        history_limit: int = MAX_PUBLIC_HISTORY,
    ):
        self.model = model or os.environ.get("HEXSWEEPER_MODEL", DEFAULT_MODEL)
        self.timeout = timeout
        if history_mode not in ("observation_only", "bounded"):
            raise ValueError("history_mode must be observation_only or bounded")
        if isinstance(history_limit, bool) or not isinstance(history_limit, int) or not (
            1 <= history_limit <= MAX_PUBLIC_HISTORY
        ):
            raise ValueError("history_limit must be between 1 and 8")
        self.history_mode = history_mode
        self.history_limit = history_limit

    def choose_action(
        self,
        observation: dict[str, Any],
        legal_actions: list[dict[str, Any]],
        history: list[dict[str, Any]] | None = None,
    ) -> Decision:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ModelCallError(
                "OPENAI_API_KEY is not set. Add it to the local environment to use model play."
            )
        skill = self._load_skill()
        if self.history_mode == "bounded":
            skill += (
                "\n\nThis run includes up to {} prior public actions and results in "
                "public_history. Use that bounded history only to organize reasoning; "
                "it cannot reveal hidden mine locations. The current observation and "
                "legal_actions remain authoritative."
            ).format(self.history_limit)
            history = list(history or [])[-self.history_limit:]
        else:
            history = None
        player_input = {
            "observation": observation,
            "legal_actions": legal_actions,
        }
        if history is not None:
            player_input["public_history"] = history
        request_body = {
            "model": self.model,
            "instructions": skill,
            "input": json.dumps(player_input, separators=(",", ":")),
            "tools": [{
                "type": "function",
                "name": "choose_move",
                "description": "Submit exactly one legal Hex Minesweeper action.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["reveal", "flag"]},
                        "q": {"type": "integer"},
                        "r": {"type": "integer"},
                    },
                    "required": ["type", "q", "r"],
                    "additionalProperties": False,
                },
                "strict": True,
            }],
            "tool_choice": "required",
            "parallel_tool_calls": False,
            "max_output_tokens": 120,
        }
        request = Request(
            os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1/responses"),
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (TimeoutError, socket.timeout) as error:
            raise ModelCallError("Model request timed out.", timed_out=True) from error
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:300]
            raise ModelCallError("Model API returned HTTP " + str(error.code) + ": " + detail) from error
        except URLError as error:
            reason = getattr(error, "reason", error)
            is_timeout = isinstance(reason, (TimeoutError, socket.timeout))
            raise ModelCallError(
                "Model request timed out." if is_timeout else "Model request failed: " + str(reason),
                timed_out=is_timeout,
            ) from error
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ModelCallError("Model API returned invalid JSON.") from error

        usage = payload.get("usage") or {}
        input_tokens = int(usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or 0)
        cost = _estimated_cost(input_tokens, output_tokens)
        for item in payload.get("output", []):
            if item.get("type") != "function_call" or item.get("name") != "choose_move":
                continue
            try:
                action = json.loads(item.get("arguments", "{}"))
            except json.JSONDecodeError as error:
                raise ModelCallError(
                    "Model returned malformed action JSON.", input_tokens=input_tokens,
                    output_tokens=output_tokens, estimated_cost_usd=cost
                ) from error
            if not isinstance(action, dict):
                raise ModelCallError(
                    "Model action must be a JSON object.", input_tokens=input_tokens,
                    output_tokens=output_tokens, estimated_cost_usd=cost
                )
            return Decision(action, input_tokens, output_tokens, cost)
        raise ModelCallError(
            "Model response did not contain choose_move.", input_tokens=input_tokens,
            output_tokens=output_tokens, estimated_cost_usd=cost
        )

    @staticmethod
    def _load_skill() -> str:
        path = os.path.join(os.path.dirname(__file__), "skills", "hex-minesweeper-player", "SKILL.md")
        with open(path, "r", encoding="utf-8") as skill_file:
            return skill_file.read()


def _estimated_cost(input_tokens: int, output_tokens: int) -> float | None:
    """Estimate cost only when dated per-token rates are explicitly configured."""
    input_rate = os.environ.get("HEXSWEEPER_INPUT_USD_PER_MILLION")
    output_rate = os.environ.get("HEXSWEEPER_OUTPUT_USD_PER_MILLION")
    if (
        input_rate is None
        or output_rate is None
        or not os.environ.get("HEXSWEEPER_PRICING_AS_OF")
        or not os.environ.get("HEXSWEEPER_PRICING_SOURCE")
    ):
        return None
    try:
        input_rate_value = float(input_rate)
        output_rate_value = float(output_rate)
        if (
            not math.isfinite(input_rate_value)
            or not math.isfinite(output_rate_value)
            or input_rate_value < 0
            or output_rate_value < 0
        ):
            return None
        return (
            input_tokens * input_rate_value + output_tokens * output_rate_value
        ) / 1_000_000
    except ValueError:
        return None


def pricing_metadata() -> dict[str, Any]:
    """Return the declared price provenance attached to estimated costs."""
    configured = _estimated_cost(0, 0) is not None
    return {
        "as_of": os.environ.get("HEXSWEEPER_PRICING_AS_OF"),
        "source": os.environ.get("HEXSWEEPER_PRICING_SOURCE"),
        "input_usd_per_million": os.environ.get("HEXSWEEPER_INPUT_USD_PER_MILLION"),
        "output_usd_per_million": os.environ.get("HEXSWEEPER_OUTPUT_USD_PER_MILLION"),
        "complete": configured,
    }
