import unittest
import json
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

    def test_model_route_requires_an_explicit_recording_session(self):
        ordinary_session = EpisodeRunner(123)
        recording_session = EpisodeRunner(124, model_playback_enabled=True)
        self.assertFalse(Handler._model_playback_allowed(ordinary_session))
        self.assertTrue(Handler._model_playback_allowed(recording_session))

        handler = Handler.__new__(Handler)
        handler.path = "/api/model/step"
        handler._read_json = lambda: {"session": "ordinary"}
        responses = []
        handler._send_json = lambda status, payload: responses.append((status, payload))
        ordinary_session.model_step = Mock()
        with patch.object(Handler, "_get_session", return_value=ordinary_session):
            with patch.object(Handler, "_get_session_guard", return_value=Lock()):
                handler.do_POST()
        self.assertEqual(responses[0][0], 403)
        ordinary_session.model_step.assert_not_called()


if __name__ == "__main__":
    unittest.main()
