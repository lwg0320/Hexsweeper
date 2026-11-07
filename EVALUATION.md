# Evaluation plan, results, and evidence status

**Suite declared:** 2026-10-26, before live model comparison or prompt tuning. On 2026-11-06, after the independent review fixes, both Claude configurations and the baseline ran the full declared and held-out suite against the current local working tree based on game revision 0c494f6. The tree was dirty, so the trace describes this local candidate rather than an immutable submitted commit; rerun after the final course copy/commit.

The Claude request uses Anthropic's five-minute ephemeral prompt cache for the static player instructions and move-tool prefix; per-turn board observations remain uncached. The live traces report cache reads and writes, confirming cache activity. There was no cache-disabled control, so this evaluation does not estimate savings caused by caching.

**Submission status: incomplete.** Paired live results and traces for both model configurations are recorded below. A passing GitHub Actions run on the course PR version is still required. The separate gameplay recording can show the deterministic Game playing agent and needs no model API. Local tests and mocked model calls are not GitHub Actions evidence.

## Question

On the same seeded Hex Minesweeper boards, how often does the model-driven player clear the board compared with the constraint-solving baseline? This is a small classroom comparison, not a claim of statistical certainty.

## Fixed suite

Each case uses the medium map (radius 3, 37 cells, 6 mines) and a shared initial reveal of the center cell at axial coordinate (0, 0). The board is generated from the listed seed and opening, then both players receive the same public observation and legal actions. The website also offers small and large maps; the declared comparison stays on medium so its cases remain comparable to the original runs. Each player configuration is planned for two episodes per case. The baseline uses the same state and has no model-call budget advantage; it is deterministic and uses no hidden state.

| Split | Seed | Situation |
|---|---:|---|
| Declared suite | 1401 | Center opens on clue 2; baseline's first corner probe reveals one numbered cell |
| Declared suite | 1402 | Center opens on clue 2; same public start clue, but baseline's first corner probe opens a 10-cell zero region |
| Declared suite | 1403 | Center opens on clue 1; baseline's first corner probe reveals a clue 2 |
| Held out | 9101 | Center opens on clue 3; baseline's first corner probe opens a 16-cell region |
| Held out | 9102 | Center opens on clue 1; baseline's first corner probe opens a 22-cell region |

These labels describe distinct seeded layouts and public play patterns. In each trial both players receive the same seed, center opening, public observation, and legal actions. The model never receives a seed or hidden mine layout. Held-out seeds are reserved for final evaluation and must not be used for prompt or solver tuning.

## Design choices and alternatives

| Choice | Selected approach and alternative considered |
|---|---|
| Grid | Use six-neighbor hexes rather than the reference game's usual square grid with eight neighbors. This is the defining adaptation; the remaining Minesweeper loop stays small and recognizable. |
| Board sizes | Offer three presets with the same rules rather than one fixed board. The presets let a human compare scale without adding mechanics; if scope had to shrink, the small and large presets are the first cuts. |
| Actions and rules | Keep reveal and flag actions; omit chording and the question-mark state. This gives the player-agent a short, explicit legal-action vocabulary instead of importing every optional control from richer Minesweeper versions. |
| Opening | Guarantee that the first reveal is safe, but do not guarantee a zero region. This avoids an immediate first-move loss while preserving deduction and guessing; a forced zero would reveal substantially more of the board. |
| Baseline | Use a constraint solver with subset deductions and exact probability enumeration on small frontiers instead of a random legal-move baseline. Random moves would be a weak competitor for a deduction puzzle and would make the comparison less informative. |
| Memory | Compare observation-only Claude with an eight-action public-history variant rather than evaluating just one prompt setup. The current observation retains all revealed clues and flags, so history adds no hidden information; the experiment checks whether a short record still helps reasoning. It did not improve wins in this suite. |
| Suite size | Use three declared seeds and two held-out seeds with two trials each rather than a much larger, more expensive evaluation. This is a bounded classroom experiment; outcomes are reported as case results, not a general skill estimate. |

## Player configurations and limits

- Game-code revision for the current live comparison: 0c494f6; the trace header records that the working tree was dirty.
- Baseline: choose_solver_action from hex_minesweeper/solver.py, using visible clue constraints, subset deductions, and exact probability enumeration on small frontiers.
- Recording distinction: the website's **Game playing agent** is this deterministic baseline. The three-to-five-minute no-API gameplay video shows that agent; it is separate from and does not replace a live model comparison.
- Model: the Anthropic Claude Messages API player in hex_minesweeper/model_agent.py, configured by HEXSWEEPER_MODEL (default claude-haiku-5-5) and the reusable skill at hex_minesweeper/skills/hex-minesweeper-player/SKILL.md.
- Model tools: one strict choose_move function; no shell, file, browser, or evaluator tools.
- Memory comparison: model receives only the current observation and legal actions. model-history additionally receives the last eight public actions, their public results, and changed coordinates. Every revealed clue and current flag is retained in the observation, so history is expected to add no information; the live comparison is meant to test whether it still helps the model reason.
- Limits: 80 decision steps, 80 model calls, and 20 seconds per call. Each player move and model attempt consumes one step; failed calls consume both a step and a call. A fallback move resolves the failed decision without an extra step. An invalid model action gets one retry; if that retry is invalid or fails, or no retry slot remains, the runner applies a seeded-random legal move. Initial provider errors/timeouts still end the episode.
- Report for each configuration: wins, losses, incomplete episodes and reasons, actions actually applied, decision steps, illegal actions, fallback actions, failures/timeouts, model calls, latency, regular input tokens, cache-write tokens, cache-read tokens, output tokens, and dated estimated cost.
- Cost provenance: for live runs, configure HEXSWEEPER_INPUT_USD_PER_MILLION, HEXSWEEPER_OUTPUT_USD_PER_MILLION, HEXSWEEPER_CACHE_WRITE_USD_PER_MILLION, HEXSWEEPER_CACHE_READ_USD_PER_MILLION, HEXSWEEPER_PRICING_AS_OF, and HEXSWEEPER_PRICING_SOURCE from current rates for the selected model. The evaluator uses separate rates for regular input, cache creation, cache reads, and output. Cost is unknown if base rates or dated source are absent/invalid, or if a response reports cache tokens without the corresponding cache rate. No provider pricing was used for the baseline-only run.

## Results

The final live comparison used both model configurations on the same three declared seeds (two trials each) and two held-out seeds (two trials each), alongside the deterministic baseline. All 10 baseline episodes were wins. All 10 observation-only model episodes and all 10 bounded-history episodes were losses by mine reveal. There were no illegal selections, fallbacks, provider failures, or timeouts in this final run. An earlier pre-fix run had one invalid selection; it was retried successfully and is retained as historical evidence in the earlier trace.

“Actions applied” counts game-changing player or fallback moves and excludes the shared opening. “Decision steps” is the runner's budget counter: it includes each model request attempt, including an invalid selection, while a successful retry or fallback may apply only one move. The two measures match for the deterministic baseline because it has no invalid attempts.

| Split | Player | Trials | Wins / losses / incomplete | Mean actions applied | Mean decision steps | Illegal actions | Fallback actions | Failures / timeouts | Mean model calls | Mean latency (ms) | Total input / cache-write / cache-read / output tokens | Dated estimated cost |
|---|---|---:|---|---:|---:|---:|---:|---|---:|---|---|---|
| Declared | Baseline | 6 | 6 / 0 / 0 | 14 | 14 | 0 | 0 | 0 / 0 | 0 | n/a | 0 / 0 / 0 / 0 | $0.00 (no provider calls) |
| Declared | Model, observation-only | 6 | 0 / 6 / 0 | 2.67 | 2.67 | 0 | 0 | 0 / 0 | 2.67 | 910.9 | 35,196 / 1,607 / 24,105 / 1,195 | $0.004559 |
| Declared | Model, bounded history | 6 | 0 / 6 / 0 | 2.83 | 2.83 | 0 | 0 | 0 / 0 | 2.83 | 1,003.1 | 40,223 / 1,676 / 26,816 / 1,273 | $0.005136 |
| Held out | Baseline | 4 | 4 / 0 / 0 | 11 | 11 | 0 | 0 | 0 / 0 | 0 | n/a | 0 / 0 / 0 / 0 | $0.00 (no provider calls) |
| Held out | Model, observation-only | 4 | 0 / 4 / 0 | 2.25 | 2.25 | 0 | 0 | 0 / 0 | 2.25 | 980.1 | 18,448 / 0 / 14,463 / 673 | $0.002326 |
| Held out | Model, bounded history | 4 | 0 / 4 / 0 | 1.75 | 1.75 | 0 | 0 | 0 / 0 | 1.75 | 991.7 | 16,369 / 0 / 11,732 / 524 | $0.002016 |

The complete final paired trace has 30 episodes (10 per player), including outcomes, per-move actions, invalid selections, model calls, latency, token usage, and estimated cost. It was recorded on 2026-11-06 from dirty working tree revision 0c494f6 after the malformed-coordinate fix. See [evaluation/live-comparison-final-2026-11-06.jsonl](evaluation/live-comparison-final-2026-11-06.jsonl). Haiku 5.5 pricing uses rates checked on 2026-11-06 from Anthropic's [official model pricing](https://platform.claude.com/docs/en/models/haiku-5-5/overview): $0.10/M input, $0.50/M output, $0.125/M five-minute cache write, and $0.01/M cache read. Total estimated cost for the final run was $0.006885 for observation-only and $0.007153 for bounded history ($0.014038 overall). Costs are estimates from reported usage and those dated rates.

The earlier successful pre-fix trace is retained at [evaluation/live-comparison-2026-11-06.jsonl](evaluation/live-comparison-2026-11-06.jsonl); it is not used for the final table above. The initial network-restricted attempt failed DNS before reaching Anthropic, received no tokens, and incurred no provider cost. Its diagnostic trace is saved separately at [evaluation/live-comparison-declared-2026-11-06.jsonl](evaluation/live-comparison-declared-2026-11-06.jsonl) and is excluded from the paired results.

Reproduce the baseline-only trials from the project root with:

    python3 -m hex_minesweeper.evaluate --players baseline --seeds 1401,1402,1403,9101,9102 --trials 2

To rerun the live comparison, first put the API key in the ignored `.env` file as described in `README.md`. The following command records all three players to a new trace from the project root (the dated rate values below are the rates used for this run and should be updated for future runs):

    HEXSWEEPER_INPUT_USD_PER_MILLION=0.10 HEXSWEEPER_OUTPUT_USD_PER_MILLION=0.50 HEXSWEEPER_CACHE_WRITE_USD_PER_MILLION=0.125 HEXSWEEPER_CACHE_READ_USD_PER_MILLION=0.01 HEXSWEEPER_PRICING_AS_OF=2026-11-06 HEXSWEEPER_PRICING_SOURCE=https://platform.claude.com/docs/en/models/haiku-5-5/overview python3 -m hex_minesweeper.evaluate --players baseline,model,model-history --seeds 1401,1402,1403,9101,9102 --trials 2 > evaluation/live-comparison-final-2026-11-06.jsonl

The small suite gives a clear result for these cases, not a general estimate of Minesweeper ability. The deterministic constraint solver won all 10 episodes; Claude lost all 20, usually within two or three applied moves. Bounded history did not improve wins. The final trace records no invalid actions, fallbacks, provider failures, or timeouts; the earlier pre-fix trace preserves the invalid selection and its successful retry. The full JSONL preserves all episode traces and failures.

## CI evidence

On 2026-11-06, the local checkout at game-code revision 0c494f6 passed all 32 unit tests under Python 3.8.0. The command node --check hex_minesweeper/static/app.js also exited successfully under Node v24.21.0. The checks cover geometry, secrecy boundaries, safe opening, zero expansion, flags, legal and illegal actions, terminal outcomes, solver deductions, model failures/timeouts, runner limits, and the latest server action event.

After the independent review fix for malformed coordinates, the current local working tree passed all 45 unit tests on 2026-11-06 under Python 3.8.0. The suite includes invalid-then-valid retry, float-coordinate rejection before game mutation, repeated invalid output, retry call failure, no-budget-for-retry, action-versus-step accounting, and the server's missing-key status. `node --check hex_minesweeper/static/app.js` and `git diff --check` passed. These are local checks of an uncommitted tree, not GitHub Actions evidence. The deterministic tests and syntax check do not make live Claude calls.

A local browser smoke check on 2026-11-06 showed the default medium board with 37 hidden hexes, an in-play status, the size selector, and both agent controls. No agent move was requested. The server-reported Claude-ready state does not establish model-call or prompt-cache behavior.

The repository contains .github/workflows/ci.yml and the course-scoped .github/workflows/midterm-lwg0320.yml. Both specify Ubuntu 24.04 and Python 3.8/3.12; the course workflow also checks browser JavaScript from midterms/lwg0320/. These local results are not a GitHub Actions result. No passing Actions run for the course PR version is linked here yet. After copying the project into the course repository, run setup, play, tests, and evaluation from a fresh clone of the PR head, then link the Actions run and record the exact PR revision here.

## Limitations

**Reflection draft: review this wording and change anything that does not reflect your experience before submitting.** I kept the board small and used a safe first reveal, but it can show only a clue rather than open a zero region. I watched a friend play all three map sizes without helping. They hesitated after an early reveal gave little information and said the game felt relatively easy. I did not change the rules after this one informal session; I would clarify that a safe first reveal may expose only a clue. I did not record the session date, duration, or episode outcomes, so I do not claim them here. My comparison covers only three declared and two held-out seeds, with two trials each; it does not establish general Minesweeper strength. The deterministic baseline won all 10 episodes, while both Claude configurations lost all 10 in the final run. An invalid move in the earlier pre-fix run was retried successfully; the final run had no illegal actions, live-call failures, or timeouts. The traces report cache read/write tokens, but I did not run a cache-disabled control. A timed-out provider worker is not forcibly cancelled and a late call could still incur cost, though no timeout occurred in this suite. See [RECORDING-CHECKLIST.md](RECORDING-CHECKLIST.md) for the recording steps.
