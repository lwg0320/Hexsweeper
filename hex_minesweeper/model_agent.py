"""Server-side Claude Messages API adapter with one constrained move tool."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import os
import socket
import ssl
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import load_project_env

load_project_env()


def _configure_certifi_fallback() -> None:
    """Use certifi only when no explicit or usable OpenSSL CA path exists."""
    if os.environ.get("SSL_CERT_FILE") or os.environ.get("SSL_CERT_DIR"):
        return
    paths = ssl.get_default_verify_paths()
    has_default_file = bool(paths.cafile and os.path.isfile(paths.cafile))
    has_default_dir = False
    if paths.capath and os.path.isdir(paths.capath):
        with os.scandir(paths.capath) as entries:
            has_default_dir = next(entries, None) is not None
    if has_default_file or has_default_dir:
        return
    try:
        import certifi
    except ImportError:
        return
    os.environ["SSL_CERT_FILE"] = certifi.where()


_configure_certifi_fallback()

DEFAULT_MODEL = "claude-haiku-5-5"
ANTHROPIC_API_VERSION = "2026-10-21"
MAX_PUBLIC_HISTORY = 8


class ModelCallError(RuntimeError):
    def __init__(
        self, message: str, *, timed_out: bool = False, input_tokens: int = 0,
        output_tokens: int = 0, estimated_cost_usd: float | None = None,
        cache_creation_input_tokens: int = 0, cache_read_input_tokens: int = 0,
    ):
        super().__init__(message)
        self.timed_out = timed_out
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.estimated_cost_usd = estimated_cost_usd
        self.cache_creation_input_tokens = cache_creation_input_tokens
        self.cache_read_input_tokens = cache_read_input_tokens


@dataclass(frozen=True)
class Decision:
    action: dict[str, Any]
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float | None = None
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


class ModelAgent:
    """Ask Claude for exactly one legal game action."""

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
        rejected_action: dict[str, Any] | None = None,
    ) -> Decision:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            raise ModelCallError(
                "ANTHROPIC_API_KEY is not set. Add your Claude API key to the local .env file and restart the server."
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
        if rejected_action is not None:
            player_input["previous_invalid_action"] = rejected_action
        request_body = {
            "model": self.model,
            "max_tokens": 120,
            # Cache the stable skill and the tool definition that precedes it.
            # The board observation below changes each turn, so leave it uncached.
            "system": [{
                "type": "text",
                "text": skill,
                "cache_control": {"type": "ephemeral", "ttl": "5m"},
            }],
            "messages": [{
                "role": "user",
                "content": json.dumps(player_input, separators=(",", ":")),
            }],
            "tools": [{
                "name": "choose_move",
                "description": (
                    "Choose and submit exactly one action from the supplied legal_actions. "
                    "Use only the public observation and optional public_history; do not infer "
                    "or request hidden mine locations. Return the action's type, q, and r exactly."
                ),
                "strict": True,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["reveal", "flag"]},
                        "q": {"type": "integer"},
                        "r": {"type": "integer"},
                    },
                    "required": ["type", "q", "r"],
                    "additionalProperties": False,
                },
            }],
            "tool_choice": {
                "type": "tool",
                "name": "choose_move",
                "disable_parallel_tool_use": True,
            },
        }
        headers = {
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
            "anthropic-version": ANTHROPIC_API_VERSION,
        }
        workspace_id = os.environ.get("ANTHROPIC_WORKSPACE_ID")
        if workspace_id:
            headers["anthropic-workspace-id"] = workspace_id
        request = Request(
            os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1/messages"),
            data=json.dumps(request_body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (TimeoutError, socket.timeout) as error:
            raise ModelCallError("Claude API request timed out.", timed_out=True) from error
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:300]
            raise ModelCallError("Claude API returned HTTP " + str(error.code) + ": " + detail) from error
        except URLError as error:
            reason = getattr(error, "reason", error)
            is_timeout = isinstance(reason, (TimeoutError, socket.timeout))
            if isinstance(reason, ssl.SSLCertVerificationError):
                raise ModelCallError(
                    "TLS certificate verification failed. Repair Python's trusted CA bundle, "
                    "then restart the game server. On macOS Python 3.8, run the Python "
                    "Install Certificates command; if it lacks permission, install certifi "
                    "for your user. TLS verification remains enabled.",
                ) from error
            raise ModelCallError(
                "Claude API request timed out." if is_timeout else "Claude API request failed: " + str(reason),
                timed_out=is_timeout,
            ) from error
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ModelCallError("Claude API returned invalid JSON.") from error

        usage = payload.get("usage") or {}
        input_tokens = int(usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or 0)
        cache_creation_input_tokens = int(usage.get("cache_creation_input_tokens", 0) or 0)
        cache_read_input_tokens = int(usage.get("cache_read_input_tokens", 0) or 0)
        cost = _estimated_cost(
            input_tokens,
            output_tokens,
            cache_creation_input_tokens,
            cache_read_input_tokens,
        )
        for item in payload.get("content", []):
            if item.get("type") != "tool_use" or item.get("name") != "choose_move":
                continue
            action = item.get("input")
            if not isinstance(action, dict):
                raise ModelCallError(
                    "Claude returned a malformed action object.",
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    estimated_cost_usd=cost,
                    cache_creation_input_tokens=cache_creation_input_tokens,
                    cache_read_input_tokens=cache_read_input_tokens,
                )
            return Decision(
                action,
                input_tokens,
                output_tokens,
                cost,
                cache_creation_input_tokens,
                cache_read_input_tokens,
            )
        raise ModelCallError(
            "Claude response did not contain the choose_move tool call.",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=cost,
            cache_creation_input_tokens=cache_creation_input_tokens,
            cache_read_input_tokens=cache_read_input_tokens,
        )

    @staticmethod
    def _load_skill() -> str:
        path = os.path.join(os.path.dirname(__file__), "skills", "hex-minesweeper-player", "SKILL.md")
        with open(path, "r", encoding="utf-8") as skill_file:
            return skill_file.read()


def _estimated_cost(
    input_tokens: int,
    output_tokens: int,
    cache_creation_input_tokens: int = 0,
    cache_read_input_tokens: int = 0,
) -> float | None:
    """Estimate cost only when dated per-token rates are explicitly configured."""
    if not _has_dated_pricing_source():
        return None
    input_rate = _configured_rate("HEXSWEEPER_INPUT_USD_PER_MILLION")
    output_rate = _configured_rate("HEXSWEEPER_OUTPUT_USD_PER_MILLION")
    cache_write_rate = _configured_rate("HEXSWEEPER_CACHE_WRITE_USD_PER_MILLION")
    cache_read_rate = _configured_rate("HEXSWEEPER_CACHE_READ_USD_PER_MILLION")
    if input_rate is None or output_rate is None:
        return None
    if cache_creation_input_tokens and cache_write_rate is None:
        return None
    if cache_read_input_tokens and cache_read_rate is None:
        return None
    return (
        input_tokens * input_rate
        + output_tokens * output_rate
        + cache_creation_input_tokens * (cache_write_rate or 0)
        + cache_read_input_tokens * (cache_read_rate or 0)
    ) / 1_000_000


def _has_dated_pricing_source() -> bool:
    return bool(
        os.environ.get("HEXSWEEPER_PRICING_AS_OF")
        and os.environ.get("HEXSWEEPER_PRICING_SOURCE")
    )


def _configured_rate(name: str) -> float | None:
    raw_rate = os.environ.get(name)
    if raw_rate is None:
        return None
    try:
        rate = float(raw_rate)
    except ValueError:
        return None
    return rate if math.isfinite(rate) and rate >= 0 else None


def pricing_metadata() -> dict[str, Any]:
    """Return the declared price provenance attached to estimated costs."""
    base_rates_configured = _estimated_cost(0, 0) is not None
    cache_rates_configured = (
        _has_dated_pricing_source()
        and _configured_rate("HEXSWEEPER_INPUT_USD_PER_MILLION") is not None
        and _configured_rate("HEXSWEEPER_OUTPUT_USD_PER_MILLION") is not None
        and _configured_rate("HEXSWEEPER_CACHE_WRITE_USD_PER_MILLION") is not None
        and _configured_rate("HEXSWEEPER_CACHE_READ_USD_PER_MILLION") is not None
    )
    return {
        "as_of": os.environ.get("HEXSWEEPER_PRICING_AS_OF"),
        "source": os.environ.get("HEXSWEEPER_PRICING_SOURCE"),
        "input_usd_per_million": os.environ.get("HEXSWEEPER_INPUT_USD_PER_MILLION"),
        "output_usd_per_million": os.environ.get("HEXSWEEPER_OUTPUT_USD_PER_MILLION"),
        "cache_write_usd_per_million": os.environ.get("HEXSWEEPER_CACHE_WRITE_USD_PER_MILLION"),
        "cache_read_usd_per_million": os.environ.get("HEXSWEEPER_CACHE_READ_USD_PER_MILLION"),
        "base_rates_complete": base_rates_configured,
        "cache_rates_complete": cache_rates_configured,
        "complete": base_rates_configured and cache_rates_configured,
    }
