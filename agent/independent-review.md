# Independent review task

Review the finished project read-only. The reviewer must not have written implementation code and must have no instruction to approve it.

Inspect:

1. Whether the rules and RULE_SOURCE_MAP.md match hex_minesweeper/game.py.
2. Whether any observation, legal-action response, browser route, or model prompt leaks hidden mines or the episode seed before terminal state.
3. Whether invalid actions, model failures, timeouts, action limits, call limits, and terminal reasons are counted and reported correctly.
4. Whether the solver uses only the public interface.
5. Whether setup, tests, and evaluation commands work from a clean checkout.
6. Any concrete bugs or rubric gaps, with file and line references.

Do not edit project files. Save findings, including a clear statement of what was inspected and what could not be verified, in agent/REVIEW.md. Do not claim approval without evidence.
