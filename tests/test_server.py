import unittest
import json

from hex_minesweeper.runner import EpisodeRunner
from hex_minesweeper.server import Handler


class ServerPayloadTests(unittest.TestCase):
    def test_browser_state_payload_preserves_the_latest_action_event(self):
        runner = EpisodeRunner(123)
        transition = runner.step(
            "human", {"type": "reveal", "q": 0, "r": 0}, actor="human"
        )
        payload = Handler._state_payload("test-session", runner, transition)
        self.assertEqual(payload["event"], transition["event"])
        self.assertEqual(payload["event"]["action"], {"type": "reveal", "q": 0, "r": 0})
        self.assertNotIn("seed", payload)
        self.assertNotIn('"seed"', json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
