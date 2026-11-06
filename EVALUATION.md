# Evaluation plan and results

**Declared:** 2026-10-26, before any live model comparison or prompt tuning. The baseline was rerun on the same declared and held-out seeds on 2026-11-06; no live model comparison has occurred.

## Question

On the same seeded Hex Minesweeper boards, how often does the model-driven player clear the board compared with the constraint-solving baseline? This is a small classroom comparison, not a claim of statistical certainty.

## Fixed suite

Each evaluation case uses the medium map (radius 3, 37 cells, 6 mines) and a shared initial reveal of the center cell at axial coordinate (0, 0). The board is generated from the listed seed and that opening, then both players receive the same public observation and legal actions. The website also offers small and large maps for play; the declared comparison suite stays on medium so its cases remain comparable to the original runs. Run two live model episodes per case. The baseline uses the same state and has no model-call budget advantage; it is deterministic and uses no hidden state.

| Split | Seed | Situation |
|---|---:|---|
| Declared suite | 1401 | Center opens on clue 2; baseline's first corner probe reveals one numbered cell |
| Declared suite | 1402 | Center opens on clue 2; same public start clue, but baseline's first corner probe opens a 10-cell zero region |
| Declared suite | 1403 | Center opens on clue 1; baseline's first corner probe reveals a clue 2 |
| Held out | 9101 | Center opens on clue 3; baseline's first corner probe opens a 16-cell region |
| Held out | 9102 | Center opens on clue 1; baseline's first corner probe opens a 22-cell region |

These labels describe distinct seeded layouts and public play patterns. In each trial both players receive the same seed, center opening, public observation, and legal actions. The model never receives a seed or hidden mine layout.

The held-out seeds are reserved for final evaluation and must not be used for prompt or solver tuning.

## Player configurations and limits

- Game version: the commit being evaluated.
- Baseline: choose_solver_action from hex_minesweeper/solver.py, which uses visible clue constraints, subset deductions, and exact probability enumeration on small frontiers.
- Model: the OpenAI Responses API player in hex_minesweeper/model_agent.py, configured by HEXSWEEPER_MODEL (default gpt-6-astra) and the reusable skill at hex_minesweeper/skills/hex-minesweeper-player/SKILL.md.
- Model tools: one strict choose_move function; no shell, file, browser, or evaluator tools.
- Memory comparison: `model` receives only the current observation and legal actions. `model-history` additionally receives the last eight public actions, their public results, and changed coordinates. Every revealed clue and current flag is already retained in the observation, so the design expectation is that history adds no information; the paired live comparison will test whether it still helps the model reason. Compare these two model policies on the same seeds and trial counts.
- Episode limits: 80 actions, 80 model calls, 20 seconds per call. Failed calls count. Invalid model actions end the episode and are reported; there is no fallback.
- Primary outcome: win, loss, or incomplete terminal reason. Also report score, illegal actions, calls, action count, latency, input/output tokens, and failures.
- Cost: report dated per-million token prices used for the model on the evaluation date. Configure HEXSWEEPER_INPUT_USD_PER_MILLION, HEXSWEEPER_OUTPUT_USD_PER_MILLION, HEXSWEEPER_PRICING_AS_OF, and HEXSWEEPER_PRICING_SOURCE; if any are absent or rates are invalid, the runner reports cost as unknown. Evaluation JSONL records the declared pricing provenance.
- Human playtest and model recording: required before submission; no peer notes or recording are represented as completed in this file.

## Comparison table

No live model trials have been run. The environment used to build this project did not provide a provider key, so model results are intentionally left blank rather than fabricated. The baseline has two deterministic trials on each listed seed; repeated results are expected to match. Run the model comparison command in the README after configuring a live provider, then update the model rows from the JSONL output and add the trace link.

### Preliminary baseline smoke run

One baseline-only trial was run on each declared seed on 2026-10-26 to check that the deterministic player reaches a terminal outcome. It won 3/3 boards, lost 0, had 0 illegal actions, and used 12, 14, and 16 actions (mean 14). This is a smoke check only, not the paired comparison or held-out result. The JSONL output with full per-move traces is saved at [evaluation/baseline-smoke-2026-10-26.jsonl](evaluation/baseline-smoke-2026-10-26.jsonl); reproduce it with the baseline-only command in the README.

| Split | Player | Trials | Wins | Losses | Incomplete / failures | Illegal actions | Mean actions | Mean latency (ms) | Input / output tokens | Dated estimated cost |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Declared suite | Baseline | 6 | 6 | 0 | 0 | 0 | 14 | n/a | 0 / 0 | $0.00 |
| Declared suite | Model, observation-only | 6 | — | — | — | — | — | — | — | — |
| Declared suite | Model, bounded history | 6 | — | — | — | — | — | — | — | — |
| Held out | Baseline | 4 | 4 | 0 | 0 | 0 | 11 | n/a | 0 / 0 | $0.00 |
| Held out | Model, observation-only | 4 | — | — | — | — | — | — | — | — |
| Held out | Model, bounded history | 4 | — | — | — | — | — | — | — | — |

The 10 baseline traces (two per seed) are saved at [evaluation/baseline-two-trials-2026-11-06.jsonl](evaluation/baseline-two-trials-2026-11-06.jsonl). The results are from the local working tree, not the final course-repository commit; rerun after packaging if code changes.

## CI evidence

The deterministic checks are in `tests/` and run through the personal repository workflow and the course-scoped workflow, both on Python 3.8 and 3.12. They pin Ubuntu 24.04 so setup-python can install Python 3.8 from its manifest. The suite covers geometry, state secrecy, first reveal safety, zero expansion, flags, legal/illegal actions, terminal outcomes, solver deductions, model failures and timeouts, and runner limits. The server test invokes the model route with an ordinary session and checks that it returns 403 without calling the runner. During browser verification, a human reveal changed the board but left the status line stuck on “player is choosing a move” because the server response omitted the latest action event. The server payload now includes that event, and `tests/test_server.py` checks that it remains present; browser verification confirmed that the status reports the completed move. A separate payload assertion ensures that the private episode seed is absent.

## Limitations

The board is intentionally small, and a first reveal is safe but not guaranteed to open a zero region. The planned live suite has only three declared seeds and two held-out seeds, with two trials each; results will not establish general Minesweeper strength. The solver is algorithmic and deterministic, while model guesses can vary. The current observations preserve all past reveals and flags, so a separate persistent memory may be redundant; the bounded-history comparison remains unrun. A timed-out provider worker is not forcibly cancelled: a late call could still incur cost, but its result cannot change the episode state. Record the provider/model, prompt and skill version, game commit, API usage, dated price source, failures, latency, and trial counts. A real human playtest and 3–5 minute recording are still required; see [PLAYTEST-NOTES.md](PLAYTEST-NOTES.md) and [RECORDING-CHECKLIST.md](RECORDING-CHECKLIST.md).
