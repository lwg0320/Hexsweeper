# Evaluation plan and results

**Declared:** 2026-10-26, before any live model comparison or prompt tuning.

## Question

On the same seeded Hex Minesweeper boards, how often does the model-driven player clear the board compared with the constraint-solving baseline? This is a small classroom comparison, not a claim of statistical certainty.

## Fixed suite

Each case uses a radius-3 board, 6 mines, and a shared initial reveal of the center cell at axial coordinate (0, 0). The board is generated from the listed seed and that opening, then both players receive the same public observation and legal actions. Run two live model episodes per case. The baseline uses the same state and has no model-call budget advantage; it is deterministic and uses no hidden state.

| Split | Seed | Situation |
|---|---:|---|
| Declared suite | 1401 | Seeded mine layout after shared center opening |
| Declared suite | 1402 | Seeded mine layout after shared center opening |
| Declared suite | 1403 | Seeded mine layout after shared center opening |
| Held out | 9101 | Seeded mine layout after shared center opening |
| Held out | 9102 | Seeded mine layout after shared center opening |

The held-out seeds are reserved for final evaluation and must not be used for prompt or solver tuning.

## Player configurations and limits

- Game version: the commit being evaluated.
- Baseline: choose_solver_action from hex_minesweeper/solver.py, which uses visible clue constraints, subset deductions, and exact probability enumeration on small frontiers.
- Model: the OpenAI Responses API player in hex_minesweeper/model_agent.py, configured by HEXSWEEPER_MODEL (default gpt-6-astra) and the reusable skill at hex_minesweeper/skills/hex-minesweeper-player/SKILL.md.
- Model tools: one strict choose_move function; no shell, file, browser, or evaluator tools.
- Episode limits: 80 actions, 80 model calls, 20 seconds per call. Failed calls count. Invalid model actions end the episode and are reported; there is no fallback.
- Primary outcome: win, loss, or incomplete terminal reason. Also report score, illegal actions, calls, action count, latency, input/output tokens, and failures.
- Cost: report dated per-million token prices used for the model on the evaluation date. Configure HEXSWEEPER_INPUT_USD_PER_MILLION, HEXSWEEPER_OUTPUT_USD_PER_MILLION, HEXSWEEPER_PRICING_AS_OF, and HEXSWEEPER_PRICING_SOURCE; if any are absent or rates are invalid, the runner reports cost as unknown. Evaluation JSONL records the declared pricing provenance.
- Human playtest and model recording: required before submission; no peer notes or recording are represented as completed in this file.

## Comparison table

No live model trials have been run. The environment used to build this project did not provide an API key, so results are intentionally left blank rather than fabricated. Run the command in the README after setting a key, then paste the JSONL summary and trace links here.

### Preliminary baseline smoke run

One baseline-only trial was run on each declared seed on 2026-10-26 to check that the deterministic player reaches a terminal outcome. It won 3/3 boards, lost 0, had 0 illegal actions, and used 12, 14, and 16 actions (mean 14). This is a smoke check only, not the paired comparison or held-out result. The JSONL output with full per-move traces is saved at [evaluation/baseline-smoke-2026-10-26.jsonl](evaluation/baseline-smoke-2026-10-26.jsonl); reproduce it with the baseline-only command in the README.

| Split | Player | Trials | Wins | Losses | Incomplete / failures | Illegal actions | Mean actions | Mean latency (ms) | Input / output tokens | Dated estimated cost |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Declared suite | Baseline | — | — | — | — | — | — | — | — | — |
| Declared suite | Model | — | — | — | — | — | — | — | — | — |
| Held out | Baseline | — | — | — | — | — | — | — | — | — |
| Held out | Model | — | — | — | — | — | — | — | — | — |

## CI evidence

The deterministic checks are in tests/ and run through .github/workflows/ci.yml. They cover geometry, state secrecy, first reveal safety, zero expansion, flags, legal/illegal actions, terminal outcomes, solver deductions, model failures and timeouts, and runner limits. During browser verification, a human reveal changed the board but left the status line stuck on “player is choosing a move” because the server response omitted the latest action event. The server payload now includes that event, and tests/test_server.py checks that it remains present; browser verification confirmed that the status reports the completed move. A separate payload assertion ensures that the private episode seed is absent.

## Limitations

The board is intentionally small, and a first reveal is safe but not guaranteed to open a zero region. The model is evaluated on only three declared seeds and two held-out seeds, with two repeated live trials per declared case; results will not establish general Minesweeper strength. The solver is algorithmic and deterministic, while the model's guesses can vary. The suite, provider model, prompt/skill version, API usage, dated cost rates, failures, trial counts, and game commit must all be recorded with final results. Peer playtest notes and a recording remain to be added.
