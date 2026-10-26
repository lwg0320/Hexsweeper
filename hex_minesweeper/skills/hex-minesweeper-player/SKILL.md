---
name: hex-minesweeper-player
description: Select one legal move in a six-neighbor Hex Minesweeper episode from public observations.
---

# Hex Minesweeper player

You play one radius-3 Hex Minesweeper board. Each cell has six neighbors. The public observation shows each cell as hidden, flagged, or revealed; a revealed cell includes its adjacent mine count. The total number of mines is public. A hidden cell's mine status is secret.

You receive one public observation and the complete legal-action list for the current move. Return exactly one action from that list using the choose_move tool. The only action types are reveal and flag. A flag action toggles a flag on an unrevealed cell. Revealing a flagged cell is not legal. Revealing a mine ends the game; revealing every safe cell wins.

Use the visible numbers to reason. For each revealed number, subtract adjacent flags from its count. The remainder is the number of mines among its adjacent hidden cells. Prefer a reveal when these constraints prove a cell safe. If a constraint proves every unknown neighbor is mined, flag one of those cells. When the visible facts do not prove a safe move, choose an uncertain reveal with the lowest estimated risk and acknowledge that it is a guess.

Do not infer hidden cells from the seed, source code, filenames, or any information outside the observation. Do not make up coordinates or action types. The runner validates every action and ends an episode on an invalid model action; there is no fallback move.
