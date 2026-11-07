import json
import os
import ssl
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import URLError

from hex_minesweeper.model_agent import (
    ModelAgent,
    ModelCallError,
    _configure_certifi_fallback,
)


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
    def test_certifi_fallback_is_used_only_without_a_configured_ca_store(self):
        fake_certifi = SimpleNamespace(where=lambda: "/tmp/test-certifi.pem")
        missing_paths = SimpleNamespace(cafile=None, capath=None)
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(sys.modules, {"certifi": fake_certifi}):
                with patch(
                    "hex_minesweeper.model_agent.ssl.get_default_verify_paths",
                    return_value=missing_paths,
                ):
                    _configure_certifi_fallback()
            self.assertEqual(os.environ["SSL_CERT_FILE"], "/tmp/test-certifi.pem")

        with patch.dict(os.environ, {"SSL_CERT_FILE": "/custom/ca.pem"}, clear=True):
            _configure_certifi_fallback()
            self.assertEqual(os.environ["SSL_CERT_FILE"], "/custom/ca.pem")

    def test_tls_verification_error_has_repair_guidance(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            with patch(
                "hex_minesweeper.model_agent.urlopen",
                side_effect=URLError(ssl.SSLCertVerificationError("verify failed")),
            ):
                with self.assertRaisesRegex(ModelCallError, "Repair Python's trusted CA bundle"):
                    ModelAgent().choose_action({"cells": []}, [])

    def test_history_limit_is_bounded_to_eight(self):
        with self.assertRaises(ValueError):
            ModelAgent(history_mode="bounded", history_limit=9)
        with self.assertRaises(ValueError):
            ModelAgent(history_mode="bounded", history_limit=0)

    def test_model_receives_only_observation_and_legal_actions(self):
        action = {"type": "reveal", "q": 0, "r": 0}
        payload = {
            "content": [{
                "type": "tool_use",
                "name": "choose_move",
                "input": action,
                "id": "toolu-test",
            }],
            "usage": {
                "input_tokens": 25,
                "output_tokens": 7,
                "cache_creation_input_tokens": 510,
                "cache_read_input_tokens": 128,
            },
            "stop_reason": "tool_use",
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
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            with patch("hex_minesweeper.model_agent.urlopen", fake_urlopen):
                result = ModelAgent(timeout=9).choose_action(observation, legal_actions)

        request = captured["request"]
        request_headers = {key.lower(): value for key, value in request.header_items()}
        body_bytes = request.data.decode("utf-8")
        body = json.loads(body_bytes)
        sent_input = json.loads(body["messages"][0]["content"])
        system_block = body["system"][0]
        self.assertEqual(sent_input, {
            "observation": observation,
            "legal_actions": legal_actions,
        })
        self.assertNotIn("sk-ant-test", body_bytes)
        self.assertEqual(request_headers["authorization"], "Bearer sk-ant-test")
        self.assertEqual(request_headers["anthropic-version"], "2026-10-21")
        self.assertEqual(captured["timeout"], 9)
        self.assertEqual(body["model"], "claude-haiku-5-5")
        self.assertEqual(system_block["type"], "text")
        self.assertIn("Hex Minesweeper player", system_block["text"])
        self.assertEqual(system_block["cache_control"], {
            "type": "ephemeral",
            "ttl": "5m",
        })
        self.assertNotIn("cache_control", body["messages"][0]["content"])
        self.assertEqual(body["tool_choice"], {
            "type": "tool",
            "name": "choose_move",
            "disable_parallel_tool_use": True,
        })
        self.assertEqual(len(body["tools"]), 1)
        self.assertEqual(body["tools"][0]["name"], "choose_move")
        self.assertTrue(body["tools"][0]["strict"])
        self.assertEqual(result.action, action)
        self.assertEqual(result.input_tokens, 25)
        self.assertEqual(result.output_tokens, 7)
        self.assertEqual(result.cache_creation_input_tokens, 510)
        self.assertEqual(result.cache_read_input_tokens, 128)

    def test_missing_action_tool_is_a_model_call_failure(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            with patch(
                "hex_minesweeper.model_agent.urlopen",
                lambda request, timeout: FakeResponse({"content": [], "usage": {}}),
            ):
                with self.assertRaisesRegex(ModelCallError, "choose_move"):
                    ModelAgent().choose_action({"cells": []}, [])

    def test_retry_prompt_includes_the_rejected_action(self):
        legal_action = {"type": "reveal", "q": 0, "r": 0}
        rejected_action = {"type": "reveal", "q": 99, "r": 99}
        captured = {}

        def fake_urlopen(request, timeout):
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeResponse({
                "content": [{
                    "type": "tool_use",
                    "name": "choose_move",
                    "input": legal_action,
                }],
                "usage": {},
            })

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            with patch("hex_minesweeper.model_agent.urlopen", fake_urlopen):
                ModelAgent().choose_action(
                    {"cells": []}, [legal_action], rejected_action=rejected_action
                )
        sent_input = json.loads(captured["body"]["messages"][0]["content"])
        self.assertEqual(sent_input["previous_invalid_action"], rejected_action)
        self.assertEqual(sent_input["legal_actions"], [legal_action])

    def test_bounded_history_mode_sends_only_the_supplied_public_history(self):
        action = {"type": "reveal", "q": 0, "r": 0}
        payload = {
            "content": [{
                "type": "tool_use",
                "name": "choose_move",
                "input": action,
                "id": "toolu-test",
            }],
            "usage": {},
        }
        captured = {}

        def fake_urlopen(request, timeout):
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeResponse(payload)

        observation = {"radius": 2, "mine_count": 3, "cells": []}
        legal_actions = [action]
        history = [{
            "action": {"type": "flag", "q": 1, "r": 0},
            "result": "flagged",
            "changed": [],
        }]
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            with patch("hex_minesweeper.model_agent.urlopen", fake_urlopen):
                ModelAgent(history_mode="bounded").choose_action(
                    observation, legal_actions, history=history
                )

        body = captured["body"]
        sent_input = json.loads(body["messages"][0]["content"])
        self.assertEqual(sent_input["public_history"], history)
        self.assertEqual(sent_input["observation"], observation)
        self.assertEqual(sent_input["legal_actions"], legal_actions)
        self.assertIn("up to 8 prior public actions", body["system"][0]["text"])

    def test_optional_workspace_id_is_sent_only_as_a_header(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["request"] = request
            return FakeResponse({
                "content": [{
                    "type": "tool_use",
                    "name": "choose_move",
                    "input": {"type": "flag", "q": 1, "r": 0},
                }],
                "usage": {},
            })

        with patch.dict(os.environ, {
            "ANTHROPIC_API_KEY": "sk-ant-test",
            "ANTHROPIC_WORKSPACE_ID": "wrkspc-test",
        }):
            with patch("hex_minesweeper.model_agent.urlopen", fake_urlopen):
                ModelAgent().choose_action({"cells": []}, [])
        request = captured["request"]
        headers = {key.lower(): value for key, value in request.header_items()}
        self.assertEqual(headers["anthropic-workspace-id"], "wrkspc-test")
        self.assertNotIn("wrkspc-test", request.data.decode("utf-8"))

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
            self.assertIsNone(_estimated_cost(1000, 500, 100, 200))
        with patch.dict(os.environ, {
            "HEXSWEEPER_INPUT_USD_PER_MILLION": "2",
            "HEXSWEEPER_OUTPUT_USD_PER_MILLION": "4",
            "HEXSWEEPER_CACHE_WRITE_USD_PER_MILLION": "2.5",
            "HEXSWEEPER_CACHE_READ_USD_PER_MILLION": "0.2",
            "HEXSWEEPER_PRICING_AS_OF": "2026-10-26",
            "HEXSWEEPER_PRICING_SOURCE": "test price sheet",
        }, clear=True):
            self.assertEqual(_estimated_cost(1000, 500, 100, 200), 0.00429)


if __name__ == "__main__":
    unittest.main()
