# Independent review report

**Review date:** 2026-10-26
**Reviewer boundary:** I did not write the game implementation. This report records an evidence-based review; it is not an unconditional approval.

## Scope and evidence

I reviewed the rules and observation interface in `hex_minesweeper/game.py`, the solver in `hex_minesweeper/solver.py`, the episode runner in `hex_minesweeper/runner.py`, the model adapter in `hex_minesweeper/model_agent.py`, the HTTP server and browser client in `hex_minesweeper/server.py` and `hex_minesweeper/static/app.js`, the tests, `RULE_SOURCE_MAP.md`, `README.md`, `EVALUATION.md`, the agent configuration, and the peer-playtest template. I also checked the cited [KMines Handbook](https://docs.kde.org/trunk_kf6/en/kmines/kmines/kmines.pdf) and [Atari End User License Agreement](https://atari.com/pages/end-user-license-agreement) on the review date.

I ran `python3 -m unittest discover -s tests -v`; all 25 tests passed. This included the updated step and model-call limit tests. I did not edit implementation files.

## Findings

### Hidden-state boundary — no direct leak found

`Game.observe` omits seed and mine information before an in-game terminal state (`hex_minesweeper/game.py:79-118`). Legal actions are computed from revealed and flagged cells, not mine placement (`game.py:120-132`). The website state payload contains session, public observation, legal actions, outcome, metrics, trace, and event, but no seed (`hex_minesweeper/server.py:133-146`); a default reset generates its seed server-side (`server.py:60-72`). The browser no longer receives or displays a seed. The model adapter serializes only the observation and legal actions, plus the reusable skill instructions, and supplies one strict `choose_move` tool (`hex_minesweeper/model_agent.py:53-80`). Tests assert the server payload excludes the seed and that the model request contains only the player interface data (`tests/test_server.py:9-18`, `tests/test_model_agent.py:24-64`).

Mine locations are revealed after an in-game win or loss; runner timeouts, limits, and provider failures remain incomplete episodes without disclosing the mine map (`game.py:79-106`, `runner.py:57-75,127-144,227-240`). This matches `RULE_SOURCE_MAP.md:15,18-19`.

### Runner limits and error paths — explicit; ordering update fixes final-step action

The runner counts submitted actions and model calls, gives failed model turns a step and call, records invalid model actions, and reports explicit reasons for limits, provider failures, timeouts, and invalid model actions (`hex_minesweeper/runner.py:77-115,127-189,191-215`). The latest ordering change computes the baseline/model observation and legal actions before consuming the final step/call. This fixes the prior edge case where checking actions after incrementing to the limit made the final permitted decision see an empty legal-action list. The new tests cover a one-step baseline episode and a one-call model episode (`tests/test_runner.py:47-58`); both pass. A terminal game result is checked before runner limits, so a win/loss on the last allowed action remains a game outcome rather than being overwritten by an incomplete limit result (`runner.py:57-75`).

The runner enforces a wall-clock deadline around the whole agent call by running it in a daemon worker and waiting on a queue with a timeout (`runner.py:117-144`). The client also passes its configured timeout to `urlopen` (`model_agent.py:90-103`). The slow-agent test verifies that the runner returns with `model_timeout` within the short deadline (`tests/test_runner.py:74-81`). One residual limitation is that a worker already past the deadline is not cancelled; it can remain alive or finish later. It cannot mutate runner state, but a delayed external request could still consume resources or incur provider cost after the episode is marked timed out. The runner reports cost as unknown for such a timeout.

### Pricing provenance — supported and logged, but not independently verified

Estimated cost is available only when input/output rates, an `as_of` date, and a source string are all supplied; invalid, negative, or non-finite rates are rejected (`hex_minesweeper/model_agent.py:140-177`). Evaluation headers and runner metrics include the declared provenance (`hex_minesweeper/evaluate.py:55-65`, `runner.py:242-253`). The program records user-supplied values; it does not verify that a cited source supports those rates or validate the date/source for authenticity. No rates/source or real model-cost measurements were available in this workspace.

### Rules and source map — materially consistent

The source map distinguishes handbook rules, project choices, implementation rules, and observed browser behavior (`RULE_SOURCE_MAP.md:5-21`). Its terminal-reveal statement is now scoped to in-game wins/losses (`:19`), resolving the prior mismatch with runner-level incomplete outcomes. The KMines Handbook supports the general Minesweeper clue, loss, and clearing behavior; its square-grid count is explicitly not applied to the hex geometry. The map identifies six-neighbor geometry, safe-first behavior, board size, flags, and omitted controls as code conventions or project choices. It also credits the source and states that no handbook prose/code or Atari product material was reused (`:23-27`). The current Atari EULA describes a personal, noncommercial license and restricts reproducing/adapting the Product and its content; the map’s summary is consistent with those terms. This is a source check, not legal advice.

### Browser regression — code path and regression guard are present

The server includes the latest action event in its state response, and the browser uses that event to replace the temporary “choosing a move” message after a nonterminal action (`hex_minesweeper/server.py:133-146`, `hex_minesweeper/static/app.js:135-153`). `tests/test_server.py:9-18` guards the payload field implicated in the reported regression. `EVALUATION.md:51` reports that browser verification confirmed the status update. The test covers the API payload rather than executing the browser DOM; I did not independently repeat the interactive browser check.

## Remaining gaps and limits of this review

- `EVALUATION.md:36,42-47` still has no live model trials or paired model/baseline comparison. Only a three-seed baseline smoke run is recorded (`:38-40`). Live outcomes, model failures, latency, token use, dated cost, and held-out results remain to be collected; the model/provider API was not exercised in this review.
- `PEER-PLAYTEST.md` remains an unfilled template, and `EVALUATION.md:55` says peer notes and a recording are still outstanding. `AGENT-TEAM.md` leaves the student-authored reflection for the student to complete in their own voice, including what they asked for, which recommendations they accepted or changed, what they learned from the review and peer playtest, and which limitations they chose to disclose. `agent/config.json` now records the implementation setup details and marks this review `completed_with_findings`; `AGENT-TEAM.md` also records that the read-only review is complete. The exact implementation model variant and reasoning setting were not exposed, as the configuration notes.
- I could not verify the tagged game or setup from a fresh clone: this workspace has no `.git` directory, so there is no local tag/commit to inspect and it is not a Git checkout. The test suite ran successfully in the supplied workspace, but that does not prove a fresh-clone workflow.
- I did not independently operate the browser UI, run a live model request, verify current provider pricing, or reproduce peer-playtest/recording evidence. The related claims are identified as project documentation, not independent observations by this reviewer.
