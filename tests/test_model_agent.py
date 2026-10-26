import json
import os
import unittest
from unittest.mock import patch

from hex_minesweeper.model_agent import ModelAgent, ModelCallError


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class ModelAgentTests(unittest.TestCase):
    def test_model_receives_only_observation_and_legal_actions(self):
        action = {"type": "reveal", "q": 0, "r": 0}
        payload = {
            "output": [{
                "type": "function_call",
                "name": "choose_move",
                "arguments": json.dumps(action),
            }],
            "usage": {"input_tokens": 25, "output_tokens": 7},
        }
        captured = {}

        def fake_urlopen(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeResponse(payload)

        observation = {
            "radius": 3,
            "mine_count": 6,
            "cells": [{"q": 0, "r": 0, "state": "hidden"}],
        }
        legal_actions = [action]
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            with patch("hex_minesweeper.model_agent.urlopen", fake_urlopen):
                result = ModelAgent(timeout=9).choose_action(observation, legal_actions)

        request = captured["request"]
        body = json.loads(request.data.decode("utf-8"))
        sent_input = json.loads(body["input"])
        self.assertEqual(sent_input, {
            "observation": observation,
            "legal_actions": legal_actions,
        })
        self.assertNotIn("sk-test", request.data.decode("utf-8"))
        self.assertEqual(captured["timeout"], 9)
        self.assertEqual(body["tool_choice"], "required")
        self.assertEqual(len(body["tools"]), 1)
        self.assertEqual(body["tools"][0]["name"], "choose_move")
        self.assertTrue(body["tools"][0]["strict"])
        self.assertEqual(result.action, action)
        self.assertEqual(result.input_tokens, 25)
        self.assertEqual(result.output_tokens, 7)

    def test_missing_action_tool_is_a_model_call_failure(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            with patch(
                "hex_minesweeper.model_agent.urlopen",
                lambda request, timeout: FakeResponse({"output": [], "usage": {}}),
            ):
                with self.assertRaises(ModelCallError):
                    ModelAgent().choose_action({"cells": []}, [])

    def test_estimated_cost_requires_explicit_dated_rates(self):
        from hex_minesweeper.model_agent import _estimated_cost

        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(_estimated_cost(1000, 500))
        with patch.dict(os.environ, {
            "HEXSWEEPER_INPUT_USD_PER_MILLION": "2",
            "HEXSWEEPER_OUTPUT_USD_PER_MILLION": "4",
        }, clear=True):
            self.assertIsNone(_estimated_cost(1000, 500))
        with patch.dict(os.environ, {
            "HEXSWEEPER_INPUT_USD_PER_MILLION": "2",
            "HEXSWEEPER_OUTPUT_USD_PER_MILLION": "4",
            "HEXSWEEPER_PRICING_AS_OF": "2026-10-26",
            "HEXSWEEPER_PRICING_SOURCE": "test price sheet",
        }, clear=True):
            self.assertEqual(_estimated_cost(1000, 500), 0.004)


if __name__ == "__main__":
    unittest.main()
