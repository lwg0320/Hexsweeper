# Implementation-agent configuration

## Task

Implement a small, standard Hex Minesweeper game for the midterm in this project. Keep the classic game loop and use six-neighbor geometry. Do not add power-ups, alternate game modes, or unrelated mechanics.

## Allowed work

- Read and change files inside this project.
- Run deterministic checks that do not need credentials.
- Implement the game, a player interface, a baseline, a model adapter, and documentation.

## Information boundary

The gameplay model receives only the public observation, legal actions, and reusable skill text. Never put seeds, hidden mines, source files, or evaluator information in a model request.

## Acceptance

- The web app runs locally and requires no browser API key.
- The server owns the authoritative game state and enforces episode/model-call/time limits.
- Unit tests cover rules, information boundaries, actions, outcomes, solver behavior, and limits.
- A live evaluation plan reports failures and does not invent trial results.
