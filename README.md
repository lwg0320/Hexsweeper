# Hex Minesweeper

A small Minesweeper recreation on a hex board, with six-neighbor clues, flags, safe first reveal, automatic zero-region opening, and a clear win or loss. Choose a small, medium, or large map. It includes a human-playable website, a constraint-solving baseline, and a model player that chooses moves through the same observation/action interface.

**Design:** a hex-grid adaptation of classic Minesweeper. **Starting point:** implemented from scratch; no Poolshark code or assets were reused. The current project folder is intended for `midterms/lwg0320/` in the course repository.

## Scope

Each episode uses a seeded map: small has 19 hexes and 3 mines, medium has 37 hexes and 6 mines, and large has 61 hexes and 10 mines. All use the same six-neighbor rules and safe first reveal. A clue counts mines in the six adjacent hexes. Revealing a mine loses; revealing every safe hex wins. A flag is only a marker and is not required for victory.

The intentional rule adaptation is using a hexagon with six neighbors instead of a rectangular grid with eight neighbors. Map sizes are project choices that change only board radius and mine count; there are no added game modes, power-ups, timers, or scoring rules.

## Rule/source map

The complete rule-by-rule map is in [RULE_SOURCE_MAP.md](RULE_SOURCE_MAP.md). It labels inherited rules as `manual`, implementation behavior as `code` or `observed`, unverified inferences as `assumed`, and project choices or adaptations as `design`, with evidence locators for each row.

This scope replaces the earlier Poolshark direction with a small hex-grid Minesweeper adaptation. If scope had to shrink further, remove the small and large presets first and keep the medium-board game loop and player interface.

## Setup

- Python 3.8 or newer is required.
- No third-party Python packages need to be installed; the game uses the standard library.
- For every command below, the working directory in the course repository is `midterms/lwg0320/`. In this development checkout, use the repository root.
- An OpenAI API key is needed only for live model play. Keep it in the local server environment; it is never sent to the browser.

Confirm the Python installation from the project working directory:

    python3 --version

## Run the website

Working directory: `midterms/lwg0320/` in the course repository (repository root in this development checkout):

    python3 -m hex_minesweeper.server

Open <http://127.0.0.1:8000>. Click a hex to reveal it. Right-click to flag it, or use Flag mode on a touchscreen. The server keeps each board seed private so it cannot be used to reconstruct hidden mines.

The game runs locally because its server keeps authoritative state private and protects the provider key. GitHub Pages can host static files but cannot run this Python game/model server; this project targets localhost as requested.

## Play with the agents

The website's **Game playing agent** works without a model key. Use it for one move or select **Run game playing agent** to let it play. The model player remains available to the evaluation runner; its controls are not shown on the game page.

Working directory: `midterms/lwg0320/` in the course repository (repository root in this development checkout). For live model play through the recording-only page, set the key in the local environment before starting the server. Ordinary sessions cannot call the model endpoint; model play requires a session opened in recording mode. Do not paste the key into project files:

    export OPENAI_API_KEY=your_key
    python3 -m hex_minesweeper.server

For paired evaluation, use a separate terminal with the key set there. Working directory: `midterms/lwg0320/` in the course repository (repository root in this development checkout):

    export OPENAI_API_KEY=your_key
    python3 -m hex_minesweeper.evaluate --seeds 1401,1402,1403 --trials 2

Optional settings:

    export HEXSWEEPER_MODEL=gpt-6-astra
    export HEXSWEEPER_INPUT_USD_PER_MILLION=your_current_input_rate
    export HEXSWEEPER_OUTPUT_USD_PER_MILLION=your_current_output_rate
    export HEXSWEEPER_PRICING_AS_OF=YYYY-MM-DD
    export HEXSWEEPER_PRICING_SOURCE='URL or pricing document title'

Rates and their date/source are optional. Estimated cost is reported as unknown unless all four values are provided and the rates are valid nonnegative numbers. The evaluation output records the declared provenance. Do not put keys or rates in the repository. The model uses the OpenAI Responses API with one strict choose_move function and no shell, file, web, or other tools. See the [official function-calling guide](https://developers.openai.com/api/docs/guides/function-calling).

## Player interface and limits

Game exposes the five operations:

1. reset(seed) starts a deterministic episode.
2. observe(player_id) returns only visible cells, public clue values, and public counts.
3. legal_actions(player_id) lists reveal and flag actions that do not expose mine locations.
4. step(player_id, action) validates and applies one action.
5. outcome() reports ongoing, win, loss, or another explicit terminal reason.

The runner holds the authoritative game state. It ends an episode at 80 actions, 80 model calls, a 20 second wall-clock model deadline, a provider failure, or an invalid model move. Failed model calls count against both action and call limits. Invalid model moves are counted and end the episode; the runner never substitutes a fallback move. The website's model-step route accepts only sessions explicitly created in recording mode. Both model variants receive public data only: the observation-only version receives the observation and legal actions; bounded history additionally receives at most eight public actions/results. Neither receives the seed, source files, or hidden mine map.

The reusable player instructions are in hex_minesweeper/skills/hex-minesweeper-player/SKILL.md. Agent setup and reviewer status are recorded in agent/config.json.

## Test

Working directory: `midterms/lwg0320/` in the course repository (repository root in this development checkout):

    python3 -m unittest discover -s tests -v

The suite checks hex geometry, seeded board behavior, first-click safety, clue/zero expansion, flag rules, hidden-state boundaries, legal and illegal actions, terminal outcomes, solver deductions, and episode limits.

## Evaluate

The suite and held-out cases were declared before live model tuning in [EVALUATION.md](EVALUATION.md). Working directory for all commands in this section: `midterms/lwg0320/` in the course repository (repository root in this development checkout). A baseline-only run needs no API key:

    python3 -m hex_minesweeper.evaluate --players baseline --seeds 1401,1402,1403 --trials 1

Paired live evaluation uses two trials on each declared seed and runs both players from the same seed and shared safe opening:

    python3 -m hex_minesweeper.evaluate --seeds 1401,1402,1403 --trials 2

To compare the observation-only model with its bounded-history variant on the same cases:

    python3 -m hex_minesweeper.evaluate --players baseline,model,model-history --seeds 1401,1402,1403 --trials 2

Run the same players on the held-out seeds, which must not be used for prompt tuning:

    python3 -m hex_minesweeper.evaluate --players baseline,model,model-history --seeds 9101,9102 --trials 2

Set OPENAI_API_KEY before a live run. The evaluator prints JSON Lines with seed, player, outcome, limits, invalid moves, latency, token usage, estimated cost when rates are configured, and a full trace.

## CI

The course-repository workflow is `.github/workflows/midterm-lwg0320.yml`; it runs deterministic tests and checks browser JavaScript from `midterms/lwg0320/`, without secrets or live model calls. It pins Ubuntu 24.04 so the Python 3.8 matrix remains available. The general `.github/workflows/ci.yml` belongs to this standalone development repository and should not be added to the course PR.

## Team, playtest, and submission evidence

- The coding-agent instructions are in [AGENTS.md](AGENTS.md). The project implementation record is in [AGENT-TEAM.md](AGENT-TEAM.md); add the student-authored reflection before submission.
- The remaining agent-team evidence and PR steps are tracked in [agent/submission-checklist.md](agent/submission-checklist.md), with a paste-ready [PR evidence block](agent/pr-body-template.md). The reusable skill's two-session invocation log is [agent/skill-usage.md](agent/skill-usage.md).
- The independent read-only review is recorded in [agent/REVIEW.md](agent/REVIEW.md). It found no direct preterminal mine/seed leak and lists the remaining evidence gaps.
- Three separate peer activities are tracked: playtesting a partner's game during the week of November 2 and sharing notes by November 6 ([PARTNER-PLAYTEST-NOTES.md](PARTNER-PLAYTEST-NOTES.md)); a friend has played all three Hexsweeper sizes while the observer watched without helping ([PLAYTEST-NOTES.md](PLAYTEST-NOTES.md)); and the later three-classmate silent review ([SILENT-PEER-REVIEWS.md](SILENT-PEER-REVIEWS.md)).
- The recording-only model view is available at `/?recording=model`; the ordinary game page keeps only the **Game playing agent** controls. Starting live model playback sends provider requests and may incur cost.
- The human playtest notes are in [PLAYTEST-NOTES.md](PLAYTEST-NOTES.md). Live model results, a 3–5 minute recording, and the course-repository pull request remain submission work; no model results are claimed here.

## Recording

Pending: add the accessible 3–5 minute recording link here and in the course PR description after recording. Follow [RECORDING-CHECKLIST.md](RECORDING-CHECKLIST.md).

## Reuse

This project is newly written and does not copy the Atari Poolshark repository, Minesweeper source code, or third-party assets. The [KMines Handbook](https://docs.kde.org/trunk_kf6/en/kmines/kmines/kmines.pdf), chapters 2–3, is credited for the general Minesweeper rules; no handbook text or code is copied. The user-provided [Atari End User License Agreement](https://atari.com/pages/end-user-license-agreement) was checked on 2026-10-26; no Atari code, ROM, assets, or branding are used. The project code is licensed under MIT; see [LICENSE](LICENSE). The [RULE_SOURCE_MAP.md](RULE_SOURCE_MAP.md) gives the full rule-by-rule source labels, locators, assumptions, design choices, omissions, and source/reuse notes.
