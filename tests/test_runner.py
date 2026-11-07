import unittest
import time

from hex_minesweeper.model_agent import Decision, ModelCallError
from hex_minesweeper.runner import EpisodeRunner


class BrokenAgent:
    model = "test-broken"

    def __init__(self, error):
        self.error = error

    def choose_action(self, observation, legal_actions):
        raise self.error


class InvalidAgent:
    model = "test-invalid"

    def choose_action(self, observation, legal_actions):
        return Decision({"type": "reveal", "q": 99, "r": 99}, 2, 1, None)


class SequenceAgent:
    model = "test-sequence"

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = 0

    def choose_action(self, observation, legal_actions):
        response = self.responses[self.calls]
        self.calls += 1
        if isinstance(response, Exception):
            raise response
        return response


class SlowAgent:
    model = "test-slow"

    def choose_action(self, observation, legal_actions):
        time.sleep(0.5)
        return Decision(legal_actions[0])


class FirstLegalAgent:
    model = "test-first-legal"

    def choose_action(self, observation, legal_actions):
        return Decision(legal_actions[0])


class CachedUsageAgent:
    model = "test-cached-usage"

    def choose_action(self, observation, legal_actions):
        return Decision(legal_actions[0], 11, 3, 0.001, 5, 7)


class HistoryAgent:
    model = "test-history"
    history_mode = "bounded"
    history_limit = 2

    def __init__(self):
        self.history = None

    def choose_action(self, observation, legal_actions, history=None):
        self.history = history
        return Decision(legal_actions[0])


class RunnerTests(unittest.TestCase):
    def test_board_size_presets_configure_the_expected_hex_maps(self):
        expected = {
            "small": (2, 19, 3),
            "medium": (3, 37, 6),
            "large": (4, 61, 10),
        }
        for size, (radius, cell_count, mine_count) in expected.items():
            with self.subTest(size=size):
                runner = EpisodeRunner(7, board_size=size)
                observation = runner.observe()
                self.assertEqual(runner.board_size, size)
                self.assertEqual(observation["radius"], radius)
                self.assertEqual(len(observation["cells"]), cell_count)
                self.assertEqual(observation["mine_count"], mine_count)

    def test_unknown_board_size_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "small, medium, or large"):
            EpisodeRunner(7, board_size="extra-large")

    def test_bounded_history_contains_only_recent_public_actions(self):
        runner = EpisodeRunner(28, fixed_opening=(0, 0))
        first_flag = next(
            action for action in runner.legal_actions()
            if action["type"] == "flag"
        )
        runner.step("human", first_flag)
        second_flag = next(
            action for action in runner.legal_actions()
            if action["type"] == "flag" and (action["q"], action["r"]) !=
            (first_flag["q"], first_flag["r"])
        )
        runner.step("human", second_flag)

        agent = HistoryAgent()
        runner.model_step(agent)

        self.assertEqual(len(agent.history), 2)
        self.assertEqual(agent.history[-1]["action"], second_flag)
        self.assertNotIn("seed", str(agent.history))
        self.assertNotIn("mine", str(agent.history))
        self.assertEqual(runner.metrics()["model_history_mode"], "bounded")

    def test_public_history_cannot_exceed_eight_actions(self):
        runner = EpisodeRunner(123)
        with self.assertRaises(ValueError):
            runner._public_history(9)

    def test_step_budget_has_an_explicit_terminal_reason(self):
        runner = EpisodeRunner(1, max_steps=1)
        runner.step("human", {"type": "flag", "q": 0, "r": 0})
        self.assertEqual(runner.outcome()["reason"], "step_limit")
        self.assertEqual(runner.legal_actions(), [])

    def test_last_baseline_step_gets_legal_actions_before_step_limit(self):
        runner = EpisodeRunner(1, max_steps=1)
        transition = runner.baseline_step()
        self.assertEqual(runner.steps, 1)
        self.assertEqual(runner.outcome()["reason"], "step_limit")
        self.assertIsNotNone(transition["event"])

    def test_model_call_budget_has_an_explicit_terminal_reason(self):
        runner = EpisodeRunner(1, max_model_calls=1)
        runner.model_step(FirstLegalAgent())
        self.assertEqual(runner.model_calls, 1)
        self.assertEqual(runner.outcome()["reason"], "model_call_limit")

    def test_failed_model_call_consumes_call_and_step_budget(self):
        runner = EpisodeRunner(1)
        runner.model_step(BrokenAgent(ModelCallError("test failure")))
        self.assertEqual(runner.model_calls, 1)
        self.assertEqual(runner.steps, 1)
        self.assertEqual(runner.outcome()["reason"], "model_error")
        self.assertEqual(runner.trace[-1]["error"], "test failure")

    def test_model_timeout_has_explicit_terminal_reason(self):
        runner = EpisodeRunner(1)
        runner.model_step(BrokenAgent(ModelCallError("late", timed_out=True)))
        self.assertEqual(runner.outcome()["reason"], "model_timeout")
        self.assertEqual(runner.model_calls, 1)

    def test_runner_enforces_wall_clock_model_deadline(self):
        runner = EpisodeRunner(1, model_timeout_seconds=0.01)
        started = time.monotonic()
        runner.model_step(SlowAgent())
        elapsed = time.monotonic() - started
        self.assertEqual(runner.outcome()["reason"], "model_timeout")
        self.assertLess(elapsed, 0.25)
        self.assertIsNone(runner.metrics()["estimated_cost_usd"])

    def test_invalid_model_action_is_retried_and_second_failure_uses_random_fallback(self):
        runner = EpisodeRunner(1)
        actions = runner.legal_actions()
        runner.model_step(InvalidAgent())
        self.assertFalse(runner.outcome()["terminal"])
        self.assertEqual(runner.illegal_actions, 2)
        self.assertEqual(runner.model_calls, 2)
        self.assertEqual(runner.fallback_actions, 1)
        self.assertEqual(runner.metrics()["actions"], 1)
        self.assertEqual(runner.metrics()["steps"], 2)
        self.assertEqual(runner.trace[0]["action"], {"type": "reveal", "q": 99, "r": 99})
        self.assertEqual(runner.trace[0]["model_attempt"], 1)
        self.assertEqual(runner.trace[-1]["actor"], "random_fallback")
        self.assertIn(runner.trace[-1]["action"], actions)
        self.assertEqual(runner.trace[-1]["fallback_reason"], "second_invalid_action")

    def test_invalid_action_followed_by_legal_retry_does_not_fallback(self):
        runner = EpisodeRunner(2)
        first_legal_action = runner.legal_actions()[0]
        agent = SequenceAgent(
            Decision({"type": "reveal", "q": 99, "r": 99}),
            Decision(first_legal_action),
        )
        runner.model_step(agent)
        self.assertEqual(agent.calls, 2)
        self.assertEqual(runner.illegal_actions, 1)
        self.assertEqual(runner.fallback_actions, 0)
        self.assertEqual(runner.metrics()["actions"], 1)
        self.assertEqual(runner.metrics()["steps"], 2)
        self.assertEqual(runner.trace[-1]["actor"], "model")
        self.assertEqual(runner.trace[-1]["action"], first_legal_action)
        self.assertTrue(runner.trace[-1]["retried_after_invalid_action"])

    def test_float_coordinates_are_rejected_and_retried_before_game_step(self):
        runner = EpisodeRunner(18)
        legal_reveal = next(
            action for action in runner.legal_actions()
            if action["type"] == "reveal"
        )
        malformed = {
            "type": legal_reveal["type"],
            "q": float(legal_reveal["q"]),
            "r": legal_reveal["r"],
        }
        agent = SequenceAgent(Decision(malformed), Decision(legal_reveal))

        runner.model_step(agent)

        self.assertEqual(agent.calls, 2)
        self.assertEqual(runner.illegal_actions, 1)
        self.assertEqual(runner.fallback_actions, 0)
        self.assertEqual(runner.metrics()["steps"], 2)
        self.assertEqual(runner.metrics()["actions"], 1)
        self.assertEqual(runner.trace[0]["error"], "invalid_model_action")
        self.assertEqual(runner.trace[-1]["action"], legal_reveal)

    def test_retry_api_error_uses_random_fallback(self):
        runner = EpisodeRunner(3)
        actions = runner.legal_actions()
        agent = SequenceAgent(
            Decision({"type": "reveal", "q": 99, "r": 99}),
            ModelCallError("retry failed"),
        )
        runner.model_step(agent)
        self.assertEqual(runner.model_calls, 2)
        self.assertEqual(runner.illegal_actions, 1)
        self.assertEqual(runner.fallback_actions, 1)
        self.assertEqual(runner.metrics()["actions"], 1)
        self.assertEqual(runner.trace[-2]["error"], "retry failed")
        self.assertIn(runner.trace[-1]["action"], actions)

    def test_invalid_action_uses_fallback_when_model_call_budget_has_no_retry_slot(self):
        runner = EpisodeRunner(4, max_model_calls=1)
        actions = runner.legal_actions()
        runner.model_step(InvalidAgent())
        self.assertEqual(runner.model_calls, 1)
        self.assertEqual(runner.illegal_actions, 1)
        self.assertEqual(runner.fallback_actions, 1)
        self.assertIn(runner.trace[-1]["action"], actions)
        self.assertEqual(runner.outcome()["reason"], "model_call_limit")

    def test_cache_usage_is_aggregated_and_recorded_per_action(self):
        runner = EpisodeRunner(1)
        runner.model_step(CachedUsageAgent())
        metrics = runner.metrics()
        self.assertEqual(metrics["input_tokens"], 11)
        self.assertEqual(metrics["output_tokens"], 3)
        self.assertEqual(metrics["cache_creation_input_tokens"], 5)
        self.assertEqual(metrics["cache_read_input_tokens"], 7)
        model_trace = next(record for record in runner.trace if record["actor"] == "model")
        self.assertEqual(model_trace["cache_creation_input_tokens"], 5)
        self.assertEqual(model_trace["cache_read_input_tokens"], 7)
        self.assertEqual(model_trace["estimated_cost_usd"], 0.001)

    def test_baseline_completes_a_bounded_episode(self):
        runner = EpisodeRunner(33, fixed_opening=(0, 0), max_steps=80)
        while not runner.outcome()["terminal"]:
            runner.baseline_step()
        self.assertIn(runner.outcome()["reason"], (
            "mine_revealed", "all_safe_cells_revealed", "step_limit"
        ))
        self.assertLessEqual(runner.steps, 80)
        self.assertEqual(runner.metrics()["actions"], runner.steps)


if __name__ == "__main__":
    unittest.main()
