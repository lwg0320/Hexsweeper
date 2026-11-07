# Evaluation plan, results, and evidence status

**Suite declared:** 2026-10-26, before live model comparison or prompt tuning. On 2026-11-06 local time (2026-11-07 UTC), both Claude configurations and the baseline ran the full declared and held-out suite against game revision 0bb8a0a. The trace marks the working tree dirty because documentation and recording changes were uncommitted; game and test code matched revision 0bb8a0a. The complete project is committed on the local course branch `lwg0320/midterm`; a pushed PR and GitHub Actions result are still pending.

The Claude request uses Anthropic's five-minute ephemeral prompt cache for the static player instructions and move-tool prefix; per-turn board observations remain uncached. The live traces report cache reads and writes, confirming cache activity. There was no cache-disabled control, so this evaluation does not estimate savings caused by caching.

**Submission status: local package ready; PR checks pending.** Paired live results and traces for both model configurations are recorded below. A passing GitHub Actions run on the pushed course PR branch is still required. The 4:52 video in `hexsweeper-recording.mp4` shows the deterministic Game playing agent running automatically and later shows the Claude API agent; the video does not replace the paired live comparison. The fresh-clone checks below are local results, not GitHub Actions evidence.

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

- Game-code revision for the current live comparison: 0bb8a0a; the trace header records that the working tree was dirty. No game or test code differed from that revision.
- Baseline: choose_solver_action from hex_minesweeper/solver.py, using visible clue constraints, subset deductions, and exact probability enumeration on small frontiers.
- Recording distinction: the website's **Game playing agent** is this deterministic baseline. The recording shows it running without manual move selection and also contains a later Claude API-agent episode. The deterministic segment uses no model API; the recording does not replace the live comparison reported here.
- Model: the Anthropic Claude Messages API player in hex_minesweeper/model_agent.py, configured by HEXSWEEPER_MODEL (default claude-haiku-5-5) and the reusable skill at hex_minesweeper/skills/hex-minesweeper-player/SKILL.md.
- Model tools: one strict choose_move function; no shell, file, browser, or evaluator tools.
- Memory comparison: model receives only the current observation and legal actions. model-history additionally receives the last eight public actions, their public results, and changed coordinates. Every revealed clue and current flag is retained in the observation, so history is expected to add no information; the live comparison is meant to test whether it still helps the model reason.
- Limits: 80 decision steps, 80 model calls, and 20 seconds per call. Each player move and model attempt consumes one step; failed calls consume both a step and a call. A fallback move resolves the failed decision without an extra step. An invalid model action gets one retry; if that retry is invalid or fails, or no retry slot remains, the runner applies a seeded-random legal move. Initial provider errors/timeouts still end the episode.
- Report for each configuration: wins, losses, incomplete episodes and reasons, actions actually applied, decision steps, illegal actions, fallback actions, failures/timeouts, model calls, latency, regular input tokens, cache-write tokens, cache-read tokens, output tokens, and dated estimated cost.
- Cost provenance: for live runs, configure HEXSWEEPER_INPUT_USD_PER_MILLION, HEXSWEEPER_OUTPUT_USD_PER_MILLION, HEXSWEEPER_CACHE_WRITE_USD_PER_MILLION, HEXSWEEPER_CACHE_READ_USD_PER_MILLION, HEXSWEEPER_PRICING_AS_OF, and HEXSWEEPER_PRICING_SOURCE from current rates for the selected model. The evaluator uses separate rates for regular input, cache creation, cache reads, and output. Cost is unknown if base rates or dated source are absent/invalid, or if a response reports cache tokens without the corresponding cache rate. No provider pricing was used for the baseline-only run.

## Results

The final live comparison used both model configurations on the same three declared seeds (two trials each) and two held-out seeds (two trials each), alongside the deterministic baseline. All 10 baseline episodes were wins. All 10 observation-only model episodes and all 10 bounded-history episodes were losses by mine reveal. There were no illegal selections, fallbacks, provider failures, or timeouts in this run. The earlier pre-fix run had one invalid selection; it was retried successfully and is retained as historical evidence in its separate trace.

“Actions applied” counts game-changing player or fallback moves and excludes the shared opening. “Decision steps” is the runner's budget counter: it includes each model request attempt, including an invalid selection, while a successful retry or fallback may apply only one move. The two measures match for the deterministic baseline because it has no invalid attempts.

| Split | Player | Trials | Wins / losses / incomplete | Mean actions applied | Mean decision steps | Illegal actions | Fallback actions | Failures / timeouts | Mean model calls | Mean latency (ms) | Total input / cache-write / cache-read / output tokens | Dated estimated cost |
|---|---|---:|---|---:|---:|---:|---:|---|---:|---|---|---|
| Declared | Baseline | 6 | 6 / 0 / 0 | 14 | 14 | 0 | 0 | 0 / 0 | 0 | n/a | 0 / 0 / 0 / 0 | $0.00 (no provider calls) |
| Declared | Model, observation-only | 6 | 0 / 6 / 0 | 2.83 | 2.83 | 0 | 0 | 0 / 0 | 2.83 | 971.1 | 36,918 / 1,607 / 25,712 / 1,269 | $0.004784 |
| Declared | Model, bounded history | 6 | 0 / 6 / 0 | 2.67 | 2.67 | 0 | 0 | 0 / 0 | 2.67 | 940.3 | 37,928 / 1,676 / 25,140 / 1,198 | $0.004853 |
| Held out | Baseline | 4 | 4 / 0 / 0 | 11 | 11 | 0 | 0 | 0 / 0 | 0 | n/a | 0 / 0 / 0 / 0 | $0.00 (no provider calls) |
| Held out | Model, observation-only | 4 | 0 / 4 / 0 | 2.25 | 2.25 | 0 | 0 | 0 / 0 | 2.25 | 979.2 | 20,546 / 0 / 14,463 / 673 | $0.002536 |
| Held out | Model, bounded history | 4 | 0 / 4 / 0 | 2.00 | 2.00 | 0 | 0 | 0 / 0 | 2.00 | 1,060.6 | 18,824 / 0 / 13,408 / 598 | $0.002315 |

The complete final paired trace has 30 episodes (10 per player), including outcomes, per-move actions, invalid selections, model calls, latency, token usage, and estimated cost. It was recorded on 2026-11-06 local time (2026-11-07 UTC) from game revision 0bb8a0a; the trace records a dirty working tree caused by uncommitted documentation and recording changes. See [evaluation/live-comparison-final-2026-11-07.jsonl](evaluation/live-comparison-final-2026-11-07.jsonl). Haiku 5.5 pricing uses rates checked on 2026-11-06 from Anthropic's [official model pricing](https://platform.claude.com/docs/en/models/haiku-5-5/overview): $0.10/M input, $0.50/M output, $0.125/M five-minute cache write, and $0.01/M cache read. Total estimated cost for this run was $0.007320 for observation-only and $0.007168 for bounded history ($0.014488 overall). Costs are estimates from reported usage and those dated rates.

The earlier successful pre-fix trace is retained at [evaluation/live-comparison-2026-11-06.jsonl](evaluation/live-comparison-2026-11-06.jsonl); it is not used for the final table above. The initial network-restricted attempt failed DNS before reaching Anthropic, received no tokens, and incurred no provider cost. Its diagnostic trace is saved separately at [evaluation/live-comparison-declared-2026-11-06.jsonl](evaluation/live-comparison-declared-2026-11-06.jsonl) and is excluded from the paired results.

Reproduce the baseline-only trials from the project root with:

    python3 -m hex_minesweeper.evaluate --players baseline --seeds 1401,1402,1403,9101,9102 --trials 2

To rerun the live comparison, first put the API key in the ignored `.env` file as described in `README.md`. The following command records all three players to a new trace from the project root (the dated rate values below are the rates used for this run and should be updated for future runs):

    HEXSWEEPER_INPUT_USD_PER_MILLION=0.10 HEXSWEEPER_OUTPUT_USD_PER_MILLION=0.50 HEXSWEEPER_CACHE_WRITE_USD_PER_MILLION=0.125 HEXSWEEPER_CACHE_READ_USD_PER_MILLION=0.01 HEXSWEEPER_PRICING_AS_OF=2026-11-06 HEXSWEEPER_PRICING_SOURCE=https://platform.claude.com/docs/en/models/haiku-5-5/overview python3 -m hex_minesweeper.evaluate --players baseline,model,model-history --seeds 1401,1402,1403,9101,9102 --trials 2 > evaluation/live-comparison-final-2026-11-07.jsonl

The small suite gives a clear result for these cases, not a general estimate of Minesweeper ability. The deterministic constraint solver won all 10 episodes; Claude lost all 20, usually within two or three applied moves. Bounded history did not improve wins. The final trace records no invalid actions, fallbacks, provider failures, or timeouts; the earlier pre-fix trace preserves the invalid selection and its successful retry. The full JSONL preserves all episode traces and failures.

## CI evidence

On 2026-11-06, the project at game-code revision 0bb8a0a passed all 45 unit tests under Python 3.8.0. `node --check hex_minesweeper/static/app.js` also exited successfully under Node v24.21.0, and `git diff --check` passed. The tests cover geometry, secrecy boundaries, safe opening, zero expansion, flags, legal and illegal actions, terminal outcomes, solver deductions, model failures/timeouts, runner limits, invalid-then-valid retry, float-coordinate rejection before game mutation, retry failure and budget accounting, and the server's missing-key status. These are local checks, not GitHub Actions evidence. The deterministic tests and syntax check do not make live Claude calls.

A local browser smoke check on 2026-11-06 showed the default medium board with 37 hidden hexes, an in-play status, the size selector, and both agent controls. No agent move was requested. The server-reported Claude-ready state does not establish model-call or prompt-cache behavior.

The standalone development checkout contains `.github/workflows/ci.yml` and `.github/workflows/midterm-lwg0320.yml`; both use Ubuntu 24.04 and Python 3.8/3.12. For the course PR, only `.github/workflows/midterm-lwg0320.yml` belongs at the course repository root. It runs the Python suite and browser JavaScript check from `midterms/lwg0320/`.

I made a clean local clone of course commit `6b5beba`. From `midterms/lwg0320/`, Python 3.8.0 ran all 45 tests successfully; `node --check hex_minesweeper/static/app.js` passed; and the paired baseline-only evaluation completed 10/10 wins. I also started the website on `127.0.0.1:8766`; the page returned HTTP 200 and `/api/status` reported the expected missing-key state. A one-seed live smoke run from that clone completed for both baseline and Claude: the baseline won, Claude lost by revealing a mine, with one API call, no illegal actions or fallbacks, and estimated cost $0.000290. The key was read from my ignored local `.env` into process memory and was not copied into the clone.

These clean-clone checks are not a GitHub Actions result. A passing Actions run for the pushed course PR version is still required; record its link after you open and push the PR.

## Limitations

I kept the game small and made the first reveal safe, but I did not guarantee it would open a zero region. I watched a friend try all three sizes without helping. They hesitated after an early reveal gave little information and said the game felt relatively easy. I did not change the rules after this one playtest; I would make the safe-first-reveal behavior clearer in the instructions. I did not record the session date, duration, or episode outcomes, so I do not claim those details.

My comparison covers three declared and two held-out seeds, with two trials each. It shows a clear result on these cases, not general Minesweeper ability: the deterministic baseline won all 10 episodes, while both Claude configurations lost all 10. The earlier pre-fix trace records an invalid move that was retried successfully; the final run had no illegal actions, fallbacks, live-call failures, or timeouts. I did not run a cache-disabled control, so the cache token counts do not show how much caching saved. A timed-out provider worker is not forcibly cancelled and could incur a late cost, though no timeout occurred in this suite. The tests and browser check described above were local; a green course-repository Actions run is still outstanding.
