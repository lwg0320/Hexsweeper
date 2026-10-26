"""Local website and authoritative game API. Uses only the Python standard library."""

from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
from threading import Lock, RLock
from typing import Any
from urllib.parse import parse_qs, urlparse

from .game import IllegalAction
from .model_agent import ModelCallError
from .runner import EpisodeRunner

ROOT = Path(__file__).resolve().parent
SESSIONS: dict[str, EpisodeRunner] = {}
SESSION_GUARDS: dict[str, Lock] = {}
SESSIONS_LOCK = RLock()
MAX_BODY_BYTES = 1_000_000


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, directory=str(ROOT / "static"), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            self._send_json(200, {
                "ok": True,
                "model": os.environ.get("HEXSWEEPER_MODEL", "gpt-6-astra"),
                "model_key_configured": bool(os.environ.get("OPENAI_API_KEY")),
                "max_steps": 80,
                "max_model_calls": 80,
                "model_timeout_seconds": 20,
            })
            return
        if parsed.path == "/api/state":
            session_id = parse_qs(parsed.query).get("session", [""])[0]
            runner = self._get_session(session_id)
            guard = self._get_session_guard(session_id)
            if runner is None or guard is None:
                self._send_json(404, {"error": "session not found"})
                return
            with guard:
                self._send_json(200, self._state_payload(session_id, runner))
            return
        if parsed.path.startswith("/api/"):
            self._send_json(404, {"error": "unknown API route"})
            return
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            body = self._read_json()
            if parsed.path == "/api/reset":
                seed = body.get("seed")
                if seed is None or str(seed).strip() == "":
                    seed = secrets.randbelow(2**31)
                if isinstance(seed, bool) or not isinstance(seed, (int, str)):
                    self._send_json(400, {"error": "seed must be an integer or string"})
                    return
                session_id = secrets.token_urlsafe(18)
                runner = EpisodeRunner(seed)
                with SESSIONS_LOCK:
                    SESSIONS[session_id] = runner
                    SESSION_GUARDS[session_id] = Lock()
                self._send_json(200, self._state_payload(session_id, runner))
                return

            session_id = body.get("session")
            if not isinstance(session_id, str):
                self._send_json(400, {"error": "session is required"})
                return
            runner = self._get_session(session_id)
            guard = self._get_session_guard(session_id)
            if runner is None or guard is None:
                self._send_json(404, {"error": "session not found"})
                return

            with guard:
                if parsed.path == "/api/step":
                    action = body.get("action")
                    if not isinstance(action, dict):
                        self._send_json(400, {"error": "action must be an object"})
                        return
                    transition = runner.step("human", action)
                    self._send_json(200, self._state_payload(session_id, runner, transition))
                    return
                if parsed.path == "/api/baseline/step":
                    transition = runner.baseline_step()
                    self._send_json(200, self._state_payload(session_id, runner, transition))
                    return
                if parsed.path == "/api/model/step":
                    transition = runner.model_step()
                    self._send_json(200, self._state_payload(session_id, runner, transition))
                    return
                self._send_json(404, {"error": "unknown API route"})
        except IllegalAction as error:
            self._send_json(400, {"error": str(error)})
        except ModelCallError as error:
            self._send_json(502, {"error": str(error)})
        except (ValueError, json.JSONDecodeError) as error:
            self._send_json(400, {"error": str(error)})
        except Exception as error:
            self.log_error("request failed: %s", error)
            self._send_json(500, {"error": "internal server error"})

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length < 0 or length > MAX_BODY_BYTES:
            raise ValueError("request body is too large")
        raw = self.rfile.read(length) if length else b"{}"
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("request body must be a JSON object")
        return payload

    @staticmethod
    def _get_session(session_id: str) -> EpisodeRunner | None:
        with SESSIONS_LOCK:
            return SESSIONS.get(session_id)

    @staticmethod
    def _get_session_guard(session_id: str) -> Lock | None:
        with SESSIONS_LOCK:
            return SESSION_GUARDS.get(session_id)

    @staticmethod
    def _state_payload(
        session_id: str, runner: EpisodeRunner, transition: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        state = transition or runner.snapshot()
        return {
            "session": session_id,
            "observation": state["observation"],
            "legal_actions": state["legal_actions"],
            "outcome": state["outcome"],
            "metrics": state.get("metrics", runner.metrics()),
            "trace": list(runner.trace),
            "event": state.get("event"),
        }

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: Any) -> None:
        super().log_message(format, *args)


def main() -> None:
    host = os.environ.get("HEXSWEEPER_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), Handler)
    print("Hex Minesweeper is running at http://" + host + ":" + str(port))
    print("Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
