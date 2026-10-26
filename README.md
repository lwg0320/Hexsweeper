# Hex Minesweeper

A small Minesweeper recreation on a radius-3 hex board, with six-neighbor clues, flags, safe first reveal, automatic zero-region opening, and a clear win or loss. It includes a human-playable website, a constraint-solving baseline, and a model player that chooses moves through the same observation/action interface.

## Scope

One episode is one seeded 37-cell board with 6 mines. The first revealed hex is safe. A clue counts mines in the six adjacent hexes. Revealing a mine loses; revealing every safe hex wins. A flag is only a marker and is not required for victory.

The only intentional rule adaptation is using a radius-3 hexagon and six neighbors instead of a rectangular grid and eight neighbors. There are no added game modes, power-ups, timers, or scoring rules. The complete rule map and evidence labels are in [RULE_SOURCE_MAP.md](RULE_SOURCE_MAP.md).

## Requirements

- Python 3.8 or newer
- No Python packages are needed to play or run deterministic tests
- An OpenAI API key is needed only for live model play; the key stays in the local server environment and is never sent to the browser

## Run the website

From the project root:

    python3 -m hex_minesweeper.server

Open <http://127.0.0.1:8000>. Click a hex to reveal it. Right-click to flag it, or use Flag mode on a touchscreen. The server keeps each board seed private so it cannot be used to reconstruct hidden mines.

The game runs locally because its server keeps authoritative state private and protects the provider key. GitHub Pages can host static files but cannot run this Python game/model server; this project targets localhost as requested.

## Play with the agents

The constraint solver works without a model key. Use Solver move or Run solver.

For the model player, set the API key in the environment before starting the website:

    export OPENAI_API_KEY=your_key
    python3 -m hex_minesweeper.server

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

The runner holds the authoritative game state. It ends an episode at 80 actions, 80 model calls, a 20 second wall-clock model deadline, a provider failure, or an invalid model move. Failed model calls count against both action and call limits. Invalid model moves are counted and end the episode; the runner never substitutes a fallback move. The model receives only the public observation and legal-action list, not the seed, source files, or hidden mine map.

The reusable player instructions are in hex_minesweeper/skills/hex-minesweeper-player/SKILL.md. Agent setup and reviewer status are recorded in agent/config.json.

## Test

From the project root:

    python3 -m unittest discover -s tests -v

The suite checks hex geometry, seeded board behavior, first-click safety, clue/zero expansion, flag rules, hidden-state boundaries, legal and illegal actions, terminal outcomes, solver deductions, and episode limits.

## Evaluate

The suite and held-out cases were declared before live model tuning in [EVALUATION.md](EVALUATION.md). A baseline-only smoke run needs no API key:

    python3 -m hex_minesweeper.evaluate --players baseline --seeds 1401,1402,1403 --trials 1

Paired live evaluation uses two trials on each declared seed and runs both players from the same seed and shared safe opening:

    python3 -m hex_minesweeper.evaluate --seeds 1401,1402,1403 --trials 2

Set OPENAI_API_KEY before a live run. The evaluator prints JSON Lines with seed, player, outcome, limits, invalid moves, latency, token usage, estimated cost when rates are configured, and a full trace. Repeat for held-out seeds with --seeds 9101,9102; do not tune the prompt on those cases.

## CI

Pushes and pull requests run the deterministic suite using .github/workflows/ci.yml. Live model calls are intentionally not part of CI.

## Team, playtest, and submission evidence

- The project implementation record is in [AGENT-TEAM.md](AGENT-TEAM.md). Add the student-authored reflection before submission.
- The independent read-only review is recorded in [agent/REVIEW.md](agent/REVIEW.md). It found no direct preterminal mine/seed leak and lists the remaining evidence gaps.
- Human peer playtest notes, a 3–5 minute recording, live evaluation results, and the course-repository pull request remain submission work. The peer-note template is in [PEER-PLAYTEST.md](PEER-PLAYTEST.md). No live provider key or peer notes were available during implementation, so no results are claimed here.

## Reuse

This project is newly written and does not copy the Atari Poolshark repository, Minesweeper source code, or third-party assets. The [RULE_SOURCE_MAP.md](RULE_SOURCE_MAP.md) credits its Minesweeper rules source and records that the user-provided Atari EULA was checked and no Atari content was reused. The project code is licensed under MIT; see [LICENSE](LICENSE).
