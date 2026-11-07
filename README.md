# Hexsweeper

A small Minesweeper recreation on a hex board, with six-neighbor clues, flags, safe first reveal, automatic zero-region opening, and a clear win or loss. Choose a small, medium, or large map. It includes a human-playable website, a constraint-solving baseline, and a model player that chooses moves through the same observation/action interface.

**Design:** a hex-grid adaptation of classic Minesweeper. **Starting point:** implemented from scratch; no Poolshark code or assets were reused. The current project folder is intended for `midterms/lwg0320/` in the course repository.

## Scope

Each episode uses a seeded map: small has 19 hexes and 3 mines, medium has 37 hexes and 6 mines, and large has 61 hexes and 10 mines. All use the same six-neighbor rules and safe first reveal. A clue counts mines in the six adjacent hexes. Revealing a mine loses; revealing every safe hex wins. A flag is only a marker and is not required for victory.

The intentional rule adaptation is using a hexagon with six neighbors instead of a rectangular grid with eight neighbors. Map sizes are project choices that change only board radius and mine count; there are no added game modes, power-ups, timers, high scores, or bonus-scoring rules.

### State, actions, and ending

`reset(seed)` creates a board whose cells are all hidden and whose flags are empty. The server keeps the seed and mine layout private. Mine placement is deferred until the first reveal, then sampled deterministically from the seed and first-reveal coordinate while excluding that cell. The first reveal is safe but is not guaranteed to open a zero region.

The only action shapes are `{"type":"reveal","q":0,"r":0}` and `{"type":"flag","q":0,"r":0}`, where `q` and `r` are integer axial coordinates. A reveal is legal on a hidden, unflagged cell. A flag action toggles a marker on a hidden cell; flagged cells can only be unflagged, and revealed cells accept no actions. The legal-action list is generated from those public states and never checks mine locations. Revealing a zero expands through connected safe hexes. Revealing a mine loses (`mine_revealed`); revealing every safe cell wins (`all_safe_cells_revealed`). Step, model-call, timeout, and initial provider-failure endings report `step_limit`, `model_call_limit`, `model_timeout`, or `model_error`, with an incomplete result. `outcome.score` is the number of safe cells revealed, including partial progress on a loss or incomplete episode.

## Rule/source map

The map below labels each rule as `manual`, `code`, `observed`, `assumed`, or `design`, separates documented rules from project choices and implementation evidence, and gives a locator for every row. The separate [RULE_SOURCE_MAP.md](RULE_SOURCE_MAP.md) includes the source and reuse notes in full.

| Rule or behavior | Source label | Documented rule / inference / project choice | Evidence |
|---|---|---|---|
| A revealed number reports the number of mines in neighboring cells. | manual | Documented square-grid rule. | KMines Handbook, Chapter 2, “How to Play,” and Chapter 3, §3.1, “Rules”; the `_numbers` calculation in `Game._place_mines_safely` in [`game.py`](hex_minesweeper/game.py). |
| Each hex has six neighbors using the listed axial offsets. | design | Deliberate adaptation from the handbook's eight square-grid neighbors to a hex grid. | This project's rule specification in README, `NEIGHBOR_DIRECTIONS` and `neighbors` in `game.py`. |
| Reset begins with every cell hidden and no flags; mine placement waits until the first reveal. | design | Initial-state choice that supports a safe first reveal without exposing a prebuilt mine map. | This project's state specification in README; `Game.reset` and `Game.step` in `game.py`. |
| Actions are exactly `reveal` or `flag` at integer axial coordinates `q,r`; reveal applies only to hidden unflagged cells and flag toggles hidden cells. | design | Small action vocabulary keeps the core loop inspectable and leaves out chording and question-mark actions. | This project's action specification in README; `Game.legal_actions` and `Game.step` in `game.py`. |
| Revealing a mine ends the game in a loss. | manual | Documented rule. | The handbook says detonating a mine ends the game. `Game.step` and `Game.outcome`. |
| Reveal every safe cell to win; flags are not required. | manual | The handbook's objective is to uncover every non-mine square; the game applies the same objective to hexes. | KMines Handbook, Chapter 2, “Objective,” and Chapter 3, §3.1, “Rules”; `Game.outcome` in `game.py`. |
| Score is the number of safe cells revealed, including partial progress on a loss or incomplete episode. | design | Progress score makes bounded or failed episodes comparable without adding a timer or bonus scoring system. | This project's outcome specification in README; `Game.outcome` in `game.py`. |
| Revealing a zero-clue cell expands through connected safe cells. | manual | Documented square-grid behavior. | KMines Handbook, Chapter 2, “How to Play”; `Game._reveal_region` in `game.py`. |
| Zero expansion follows the six hex neighbors and stops at flags and mines. | design | Hex adaptation and traversal boundary selected for this implementation. | This project's rule specification in README; `Game._reveal_region` and `neighbors` in `game.py`. |
| A flag marks a suspected mine and is not proof that the cell contains a mine. | manual | Documented Minesweeper behavior. | KMines Handbook, Chapter 3, §3.2, “Strategies and Tips.” |
| Flagging toggles between flagged and unflagged; flagged cells cannot be revealed. | design | Action-interface choice. The project omits the handbook's question-mark state and uses one reversible flag toggle. | This project's action specification in README; `Game.legal_actions` and `Game.step` in `game.py`. |
| First reveal is safe. | design | Project choice; the reference manual does not require safe-first behavior. | `_place_mines_safely` excludes the opening cell. |
| Map size presets are small (radius 2, 19 cells, 3 mines), medium (radius 3, 37 cells, 6 mines), and large (radius 4, 61 cells, 10 mines). | design | Project choices; mine density stays close across sizes while the core rules stay the same. | `BOARD_PRESETS` and `board_coordinates` in `game.py`; the website selector starts the selected map on New board. |
| Each cell's neighbors are the six axial offsets `(1,0)`, `(-1,0)`, `(0,1)`, `(0,-1)`, `(1,-1)`, and `(-1,1)`. | design | Hex-grid geometry selected for this project; it is not part of the square-grid manual. | `NEIGHBOR_DIRECTIONS` in `game.py`. |
| The mine layout is deterministic from a private episode seed and the first-reveal coordinate, with the opening excluded. | design | Project choice for reproducible evaluation and safe first reveal. | `Game._place_mines_safely`; tests verify reproducibility and first-click safety. The seed stays out of public observations and browser responses. |
| Mines are sampled uniformly from the cells other than the first reveal. | design | Explicit generation choice for reproducible seeded boards and a guaranteed-safe first reveal; the handbook does not specify a generation distribution. | This project's rule specification in README; `random.Random.sample` in `Game._place_mines_safely`. |
| Flags cannot be placed on revealed cells, and actions on revealed cells are not legal. | code | Enforced action validation for the chosen action vocabulary. | `Game.legal_actions` and `Game.step` in `game.py`. |
| No first-click zero guarantee, chord action, question-mark state, timer, high-score table, pause mode, or separate difficulty selector. | design | Named omissions. The map-size selector is the only size preset; it changes board radius and mine count without adding a game mode or a separate difficulty setting. | The browser exposes reveal, flag, map selection, and reset only. |
| Model sees public cell states, revealed clues, public mine total, and legal actions; the bounded-history comparison also receives at most eight prior public actions/results and changed coordinates. | code | Information boundary selected for the player role. Neither model mode receives the seed, hidden mine map, repository, or evaluator tools. | `Game.observe`, `Game.legal_actions`, `EpisodeRunner._public_history`, `ModelAgent.choose_action`, and interface tests. |
| At an in-game win or loss, mine locations are shown for review. | code | Post-game display choice. Runner limit and provider-failure outcomes are incomplete episodes and do not reveal the mine map. | `Game.observe` terminal handling; `EpisodeRunner` terminal overrides. |
| Runner stops at 80 decision steps, 80 model calls, or a 20-second per-call wall-clock deadline. | code | Each player move and model attempt consumes one step; failed calls consume a step and call. A seeded-random fallback resolves the failed decision without an extra step. Initial provider failures end with explicit reasons. | `MAX_STEPS`, `MAX_MODEL_CALLS`, and `MODEL_TIMEOUT_SECONDS` in `runner.py`; tests cover limits, failures, retry, and fallback. |
| After a human reveal, the status line reports the completed action. | observed | Browser regression found during play: the board updated while the status remained “player is choosing a move.” Including the latest event in the API response fixed it. | `tests/test_server.py`; browser verification on 2026-10-26. |

This scope replaces the earlier Poolshark direction with a small hex-grid Minesweeper adaptation. If scope had to shrink further, remove the small and large presets first and keep the medium-board game loop and player interface.

I posted this scope change as a reply to my [original Week 3 discussion post](https://courseworks2.columbia.edu/courses/258228/discussion_topics/1669984?entry_id=5282356).

## Setup

- Python 3.8 or newer is required.
- No third-party Python packages need to be installed; the game uses the standard library.
- For every command below, the working directory in the course repository is `midterms/lwg0320/`. In this development checkout, use the repository root.
- A Claude API key is needed only for the Claude API agent. Store it in the local, gitignored `.env` file; it is read by the server and never sent to the browser.

Confirm the Python installation from the project working directory:

    python3 --version

No dependency installation is needed. To configure the optional Claude API player on a fresh clone, from the same working directory copy the template once, then edit `.env` to add your key:

    cp .env.example .env

Skip that copy if you only want to play the website or use the deterministic Game playing agent. If `.env` already exists, edit it without replacing it.

## Run the website

Working directory: `midterms/lwg0320/` in the course repository (repository root in this development checkout):

    python3 -m hex_minesweeper.server

Open <http://127.0.0.1:8000>. Click a hex to reveal it. Right-click to flag it, or use Flag mode on a touchscreen. The server keeps each board seed private so it cannot be used to reconstruct hidden mines.

On a fresh clone, copy `.env.example` to `.env` once, then add your Claude API key to the `ANTHROPIC_API_KEY` line. The `.env` file is ignored by Git. Restart the server after changing it. If the `.env` file already exists, edit it directly rather than replacing it.

If Python reports `CERTIFICATE_VERIFY_FAILED` for Claude requests, repair its CA bundle and restart the server. On macOS with Python from python.org, run the matching `/Applications/Python X.Y/Install Certificates.command` (for Python 3.8: `/Applications/Python 3.8/Install Certificates.command`). If that system install is not writable, run `python3 -m pip install --user certifi`; the app uses certifi only when Python has no configured CA bundle. HTTPS certificate verification stays enabled.

The game runs locally because its server keeps authoritative state private and protects the provider key. GitHub Pages can host static files but cannot run this Python game/model server; this project targets localhost as requested.

## Play with the agents

The main game page offers both players. **Game playing agent** is the deterministic solver; it works without a provider key. **Claude API agent** asks Claude to choose a move using the public board and legal actions. Use the one-move button or run either player automatically. Before its first Claude request, the page asks you to confirm that API use may incur charges. A move normally uses one request; an illegal selection may trigger one retry. Full auto-play is capped at 80 calls.

Working directory: `midterms/lwg0320/` in the course repository (repository root in this development checkout). Put your key in `.env` before starting the server. Never paste the key into the webpage, source files, or chat. The server calls Anthropic's Messages API with a single strict `choose_move` tool and gives Claude no shell, file, browser, or evaluator tools. The official references describe the [Messages API](https://platform.claude.com/docs/en/api/messages) and [strict tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use).

### What Claude receives

The system prompt is the full player instruction file at [hex_minesweeper/skills/hex-minesweeper-player/SKILL.md](hex_minesweeper/skills/hex-minesweeper-player/SKILL.md). It explains the six-neighbor rules, how to reason from visible clues and flags, when to guess, and that hidden mines must never be inferred from anything outside the observation. Each turn, Claude receives a JSON user message with this shape. This is shortened for readability; a real request has an entry for every board cell and legal move:

```json
{
  "observation": {
    "radius": 3,
    "mine_count": 6,
    "cells": [{ "q": 0, "r": 0, "state": "hidden" }],
    "revealed_safe": 0,
    "flag_count": 0,
    "first_reveal": null
  },
  "legal_actions": [
    { "type": "flag", "q": 0, "r": 0 },
    { "type": "reveal", "q": 0, "r": 0 }
  ]
}
```

The actual observation contains the public board fields and one legal-action entry for each currently legal reveal or flag. It does not contain the seed, hidden mine locations, source code, or repository contents. Claude must answer through the strict `choose_move` tool with exactly three fields: `type` (`reveal` or `flag`), integer `q`, and integer `r`. The server checks the returned action against `legal_actions`. If Claude selects an illegal move, the retry includes a `previous_invalid_action` field and tells it to choose a different listed move. If the retry is invalid or the retry call fails, the runner applies a seeded-random legal move and records the fallback in the trace. A provider failure on the initial call still ends the episode.

The website uses **observation-only** mode: each request has the current observation and legal actions, with no separate move history. The evaluation-only `model-history` variant may also receive up to eight previous public actions/results, including publicly changed coordinates. The selected model defaults to `claude-haiku-5-5`, and each request allows up to 120 output tokens.

Set `HEXSWEEPER_MODEL` in `.env` to select another model. For an API key that is not scoped to a workspace, set `ANTHROPIC_WORKSPACE_ID` as well. Prompt caching marks the stable player instructions and move-tool definition for a five-minute ephemeral cache; the changing board observation is sent uncached. The runner reports regular input, cache-write, cache-read, and output tokens separately. This configures caching but does not establish a cache hit until a live response reports cache-read tokens. See Anthropic's [prompt caching guide](https://platform.claude.com/docs/en/build-with-claude/prompt-caching).

For optional cost estimates, configure `HEXSWEEPER_INPUT_USD_PER_MILLION`, `HEXSWEEPER_OUTPUT_USD_PER_MILLION`, `HEXSWEEPER_CACHE_WRITE_USD_PER_MILLION`, `HEXSWEEPER_CACHE_READ_USD_PER_MILLION`, `HEXSWEEPER_PRICING_AS_OF`, and `HEXSWEEPER_PRICING_SOURCE` using current rates for the selected model. Cost is unknown if dated base rates are missing, or if an observed cache write/read has no corresponding configured rate. Keep API keys and pricing settings private.

## Player interface and limits

Game exposes the five operations:

1. reset(seed) starts a deterministic episode.
2. observe(player_id) returns only visible cells, public clue values, and public counts.
3. legal_actions(player_id) lists reveal and flag actions that do not expose mine locations.
4. step(player_id, action) validates and applies one action.
5. outcome() reports ongoing, win, loss, or another explicit terminal reason.

The runner holds the authoritative game state. It ends an episode at 80 decision steps, 80 model calls, a 20 second per-call wall-clock deadline, or an initial provider failure. Each player move and each model attempt consumes one decision step; a failed model call also consumes one call. A fallback move resolves the failed decision and does not consume an extra step. After one illegal model selection, the runner retries once; if the retry is invalid or fails, or the limits leave no retry slot, it applies a seeded-random legal move. Illegal attempts and fallback actions are counted and recorded separately. Both model variants receive public data only: the website's observation-only version receives the observation and legal actions; bounded history additionally receives at most eight public actions/results. Neither receives the seed, source files, or hidden mine map. The server keeps the API key on the server side.

The reusable player instructions are in hex_minesweeper/skills/hex-minesweeper-player/SKILL.md. Agent setup and reviewer status are recorded in agent/config.json.

## Test

Working directory: `midterms/lwg0320/` in the course repository (repository root in this development checkout):

    python3 -m unittest discover -s tests -v

The suite checks hex geometry, seeded board behavior, first-click safety, clue/zero expansion, flag rules, hidden-state boundaries, legal and illegal actions, retry and random fallback behavior, terminal outcomes, solver deductions, episode limits, the static cache breakpoint, cached token reporting, and cache-aware cost estimates.

## Evaluate

The suite and held-out cases were declared before live model tuning in [EVALUATION.md](EVALUATION.md). Working directory for all commands in this section: `midterms/lwg0320/` in the course repository (repository root in this development checkout). A baseline-only run needs no API key:

    python3 -m hex_minesweeper.evaluate --players baseline --seeds 1401,1402,1403 --trials 1

Paired live evaluation uses two trials on each declared seed and runs both players from the same seed and shared safe opening:

    python3 -m hex_minesweeper.evaluate --seeds 1401,1402,1403 --trials 2

To compare the observation-only model with its bounded-history variant on the same cases:

    python3 -m hex_minesweeper.evaluate --players baseline,model,model-history --seeds 1401,1402,1403 --trials 2

Run the same players on the held-out seeds, which must not be used for prompt tuning:

    python3 -m hex_minesweeper.evaluate --players baseline,model,model-history --seeds 9101,9102 --trials 2

The evaluator reads the Claude key from `.env` or the shell environment. It prints JSON Lines with seed, player, outcome, limits, invalid moves, latency, regular input/cache-write/cache-read/output token usage, estimated cost when all observed token classes have dated rates, and a full trace.

## CI

The course-repository workflow is `.github/workflows/midterm-lwg0320.yml`; it runs deterministic tests and checks browser JavaScript from `midterms/lwg0320/`, without secrets or live model calls. It pins Ubuntu 24.04 so the Python 3.8 matrix remains available. The general `.github/workflows/ci.yml` belongs to this standalone development repository and should not be added to the course PR.

## Team, playtest, and submission evidence

- The coding-agent instructions are in [AGENTS.md](AGENTS.md). [AGENT-TEAM.md](AGENT-TEAM.md) is my first-person log of the implementation agent, two skill-use sessions, and the independent review, with the decisions I made and the evidence locations.
- The remaining agent-team evidence and PR steps are tracked in [agent/submission-checklist.md](agent/submission-checklist.md), with a paste-ready [PR evidence block](agent/pr-body-template.md). The reusable skill's two-session invocation log is [agent/skill-usage.md](agent/skill-usage.md).
- A fresh, independent, read-only review of the current Claude integration, key-status UI, retry/fallback handling, information boundaries, limits, and documentation is recorded in [agent/REVIEW.md](agent/REVIEW.md). The reviewer did not edit the project or make model calls. The report records the findings, author dispositions, and the malformed-coordinate regression test.
- The revised human-playtest requirement accepts any person playing your build while you watch without helping. An anonymous friend played all three Hexsweeper sizes; the notes record their low-information early reveal, hesitation, difficulty impression, and a possible instruction change in [PLAYTEST-NOTES.md](PLAYTEST-NOTES.md). The later three-classmate silent review ([SILENT-PEER-REVIEWS.md](SILENT-PEER-REVIEWS.md)) is a separate activity after assignments are made.
- The [4:52 gameplay recording](hexsweeper-recording.mp4) shows the deterministic **Game playing agent** running without manual move selection; its episode ends on a mine, which the game displays as a terminal loss. The recording also shows an automatic Claude API-agent episode. The deterministic solver is a constraint-based player, not an LLM; it sees the public board, can still have to guess, and is bounded by the 80-decision episode limit. The Claude API agent is separate and may incur cost.
- The human playtest notes are in [PLAYTEST-NOTES.md](PLAYTEST-NOTES.md). The final live comparison in [EVALUATION.md](EVALUATION.md) covers the declared and held-out suites: all 10 baseline episodes were wins, while both Claude configurations lost all 10 episodes. The full final trace and earlier diagnostic/pre-fix traces are linked there. The final comparison cost an estimated $0.014488 at rates dated 2026-11-06. Its trace is from game revision `0bb8a0a`; the working tree was dirty only because documentation and recording changes were uncommitted.
- A fresh local clone of the course branch passed all 45 tests, the JavaScript syntax check, the baseline evaluation, and a localhost website smoke check; one live Claude smoke also ran from that clone. The course workflow still needs a passing GitHub Actions run after you push and open the PR.

## Recording

Watch or download the [4:52 gameplay recording](hexsweeper-recording.mp4) (44.3 MB). It is the compressed, GitHub-sized copy of the local `vid.mov`; only the MP4 should go into the course PR. The video visibly shows the deterministic Game playing agent running automatically and an unsuccessful mine-reveal episode, followed by a Claude API-agent episode. The narration states the solver's limits: it uses only public board information, may need to guess, and has an 80-decision episode limit. See [RECORDING-CHECKLIST.md](RECORDING-CHECKLIST.md) for recording verification details.

## Reuse

This project is newly written and does not copy the Atari Poolshark repository, Minesweeper source code, or third-party assets. The [KMines Handbook](https://docs.kde.org/trunk_kf6/en/kmines/kmines/kmines.pdf), chapters 2–3, is credited for the general Minesweeper rules; Chapter 7 identifies the handbook documentation license as the GNU Free Documentation License. No handbook prose, code, or assets are copied. The user-provided [Atari End User License Agreement](https://atari.com/pages/end-user-license-agreement) was checked on 2026-11-06; it restricts reuse of Atari product content, including its use for generative-AI development or training without written consent. No Atari code, ROM, assets, branding, or other Atari product content is used or sent to the Claude API agent. The project code is licensed under MIT; see [LICENSE](LICENSE). The [RULE_SOURCE_MAP.md](RULE_SOURCE_MAP.md) gives the full rule-by-rule source labels, locators, assumptions, design choices, omissions, and source/reuse notes.
