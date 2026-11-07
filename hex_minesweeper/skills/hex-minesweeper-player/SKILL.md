---
name: hex-minesweeper-player
description: Select one legal move in a six-neighbor Hex Minesweeper episode from public observations.
---

# Hex Minesweeper player

You play a small, medium, or large Hex Minesweeper board. Use the public observation's radius and mine count; each cell has six neighbors. The observation shows each cell as hidden, flagged, or revealed; a revealed cell includes its adjacent mine count. A hidden cell's mine status is secret.

You receive one public observation and the complete legal-action list for the current move. Return exactly one action from that list using the choose_move tool. The only action types are reveal and flag. A flag action toggles a flag on an unrevealed cell. Revealing a flagged cell is not legal. Revealing a mine ends the game; revealing every safe cell wins.

If `previous_invalid_action` appears in the input, it is the action rejected on your immediately prior attempt. Do not repeat it; choose a different action that appears in the current `legal_actions` list.

Some evaluation runs also include `public_history`, containing at most the last eight public actions and their visible results. Treat it as optional context only; the current observation and legal-action list remain authoritative.

Use the visible numbers to reason. For each revealed number, subtract adjacent flags from its count. The remainder is the number of mines among its adjacent hidden cells. Prefer a reveal when these constraints prove a cell safe. If a constraint proves every unknown neighbor is mined, flag one of those cells. When the visible facts do not prove a safe move, choose an uncertain reveal with the lowest estimated risk and acknowledge that it is a guess.

Do not infer hidden cells from the seed, source code, filenames, or any information outside the observation. Do not make up coordinates or action types. The runner validates every action, retries one invalid selection when the episode budget allows, and uses a random legal move if the retry also fails.

## Move checklist

First confirm the board's radius, mine count, visible cell states, and the exact actions currently listed as legal. Do not rely on remembered coordinates from a previous turn: the legal-action list for this turn is authoritative. For each revealed number, inspect all six neighboring cells. Subtract neighboring flags from the clue, then compare the remaining mine count with the number of hidden neighbors. A remainder of zero proves those hidden neighbors safe; an equal remainder and hidden-neighbor count proves them mined.

Combine overlapping clue constraints only when every cell in the comparison is visible in the observation. If one constraint's unknown cells are a subset of another's, subtract the smaller equation from the larger one to reason about the remaining cells. Recheck the resulting count against the number of cells before treating it as certain. Choose a legal reveal of a proven-safe cell when one exists. If several safe reveals are available, prefer one that touches useful clues or may open a zero region, but do not claim that a safe opening guarantees a large region. Flag a mine only when the visible constraints prove it; flags are reversible markers and are not needed to win, so avoid spending moves on flags that do not help the next deduction.

When no safe reveal is proven, make a guess rather than inventing certainty. Estimate risk from the overlapping visible clues, choose among legal reveal actions with the lowest supported risk, and use information value only as a tie-breaker. If the observation does not support a reliable probability comparison, state internally that the choice is uncertain and select one legal reveal. Never repeat a move already reflected in the current observation. Return only the single structured action requested by choose_move; the game server, not the model, applies it and determines whether the episode continues.
