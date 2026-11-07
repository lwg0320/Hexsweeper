import json
import os
import unittest
from threading import Lock
from unittest.mock import Mock, patch

from hex_minesweeper.runner import EpisodeRunner
from hex_minesweeper.server import Handler


class ServerPayloadTests(unittest.TestCase):
    def test_browser_state_payload_preserves_the_latest_action_event(self):
        runner = EpisodeRunner(123)
        transition = runner.step(
            "human", {"type": "reveal", "q": 0, "r": 0}, actor="human"
        )
        payload = Handler._state_payload("test-session", runner, transition)
        self.assertEqual(payload["board_size"], "medium")
        self.assertEqual(payload["event"], transition["event"])
        self.assertEqual(payload["event"]["action"], {"type": "reveal", "q": 0, "r": 0})
        self.assertNotIn("seed", payload)
        self.assertNotIn('"seed"', json.dumps(payload))

    def test_model_route_requires_explicit_session_opt_in(self):
        runner = EpisodeRunner(123)
        runner.model_step = Mock(return_value=runner.snapshot())

        def post(path):
            handler = Handler.__new__(Handler)
            handler.path = path
            handler._read_json = lambda: {"session": "normal"}
            handler.responses = []
            handler._send_json = lambda status, payload: handler.responses.append((status, payload))
            with patch.object(Handler, "_get_session", return_value=runner):
                with patch.object(Handler, "_get_session_guard", return_value=Lock()):
                    handler.do_POST()
            return handler.responses

        rejected = post("/api/model/step")
        self.assertEqual(rejected[0][0], 403)
        runner.model_step.assert_not_called()

        enabled = post("/api/model/enable")
        self.assertEqual(enabled[0], (200, {"enabled": True}))
        accepted = post("/api/model/step")
        self.assertEqual(accepted[0][0], 200)
        runner.model_step.assert_called_once_with()

    def test_status_exposes_only_whether_a_claude_key_is_configured(self):
        handler = Handler.__new__(Handler)
        handler.path = "/api/status"
        responses = []
        handler._send_json = lambda status, payload: responses.append((status, payload))
        with patch.dict(os.environ, {
            "ANTHROPIC_API_KEY": "sk-ant-private-test-value",
            "HEXSWEEPER_MODEL": "claude-test-model",
        }):
            handler.do_GET()
        payload = responses[0][1]
        self.assertEqual(responses[0][0], 200)
        self.assertTrue(payload["model_key_configured"])
        self.assertEqual(payload["provider"], "Anthropic Claude API")
        self.assertEqual(payload["model"], "claude-test-model")
        self.assertNotIn("sk-ant-private-test-value", json.dumps(payload))

    def test_status_marks_missing_or_blank_claude_key_as_not_configured(self):
        handler = Handler.__new__(Handler)
        handler.path = "/api/status"
        responses = []
        handler._send_json = lambda status, payload: responses.append((status, payload))
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "   "}):
            handler.do_GET()
        status, payload = responses[0]
        self.assertEqual(status, 200)
        self.assertFalse(payload["model_key_configured"])
        self.assertNotIn("api_key", payload)


if __name__ == "__main__":
    unittest.main()
