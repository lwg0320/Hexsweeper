"""A deterministic constraint-solving baseline that sees only public data."""

from __future__ import annotations

from itertools import product
from math import comb
from typing import Any, Tuple

Cell = Tuple[int, int]

NEIGHBOR_DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1))


def _neighbors(cell: Cell) -> tuple[Cell, ...]:
    q, r = cell
    return tuple((q + dq, r + dr) for dq, dr in NEIGHBOR_DIRECTIONS)


def _action(kind: str, cell: Cell) -> dict[str, Any]:
    return {"type": kind, "q": cell[0], "r": cell[1]}


def choose_solver_action(
    observation: dict[str, Any], legal_actions: list[dict[str, Any]]
) -> dict[str, Any]:
    """Choose a forced safe reveal when possible; otherwise minimize estimated risk."""
    if not legal_actions:
        raise ValueError("no legal actions")
    cells = {(item["q"], item["r"]): item for item in observation["cells"]}
    reveal_actions = {
        (action["q"], action["r"]): action
        for action in legal_actions if action["type"] == "reveal"
    }
    flag_actions = {
        (action["q"], action["r"]): action
        for action in legal_actions if action["type"] == "flag"
    }
    if not any(cell["state"] == "revealed" for cell in cells.values()):
        return min(reveal_actions.values(), key=lambda move: (move["q"], move["r"]))

    flags = {cell for cell, view in cells.items() if view["state"] == "flagged"}
    unknown = {cell for cell, view in cells.items() if view["state"] == "hidden"}
    constraints: list[tuple[frozenset[Cell], int]] = []
    for cell, view in cells.items():
        if view["state"] != "revealed":
            continue
        adjacent_unknown = frozenset(
            neighbor for neighbor in _neighbors(cell)
            if neighbor in unknown
        )
        adjacent_flags = sum(
            1 for neighbor in _neighbors(cell) if neighbor in flags
        )
        remaining = int(view["number"]) - adjacent_flags
        if adjacent_unknown:
            constraints.append((adjacent_unknown, remaining))

    forced_safe, forced_mines = _deduce(constraints)
    safe_choices = sorted(forced_safe.intersection(reveal_actions))
    if safe_choices:
        cell = safe_choices[0]
        return reveal_actions[cell]

    flag_choices = sorted(forced_mines.intersection(flag_actions))
    if flag_choices:
        cell = flag_choices[0]
        return flag_actions[cell]

    risks = _estimate_risks(observation, cells, unknown, flags, constraints)
    candidates = sorted(reveal_actions)
    if candidates:
        cell = min(candidates, key=lambda item: (risks.get(item, 1.0), item[0], item[1]))
        return reveal_actions[cell]

    # The only remaining legal actions are flag toggles on already flagged cells.
    # Such a position should be unusual; undo the first flag to keep play moving.
    return min(flag_actions.values(), key=lambda move: (move["q"], move["r"]))


def _deduce(
    constraints: list[tuple[frozenset[Cell], int]]
) -> tuple[set[Cell], set[Cell]]:
    safe: set[Cell] = set()
    mines: set[Cell] = set()
    current = list(constraints)
    changed = True
    while changed:
        changed = False
        for group, count in current:
            if count == 0:
                before = len(safe)
                safe.update(group)
                changed |= len(safe) != before
            elif count == len(group):
                before = len(mines)
                mines.update(group)
                changed |= len(mines) != before
        reduced: set[tuple[frozenset[Cell], int]] = set()
        for left_group, left_count in current:
            for right_group, right_count in current:
                if left_group < right_group:
                    remainder = right_group - left_group
                    count = right_count - left_count
                    if 0 <= count <= len(remainder) and remainder:
                        reduced.add((frozenset(remainder), count))
        additions = list(reduced.difference(current))
        if additions:
            current.extend(additions)
            changed = True
    return safe - mines, mines


def _estimate_risks(
    observation: dict[str, Any],
    cells: dict[Cell, dict[str, Any]],
    unknown: set[Cell],
    flags: set[Cell],
    constraints: list[tuple[frozenset[Cell], int]],
) -> dict[Cell, float]:
    """Enumerate small frontiers exactly, weighted by remaining global mines."""
    frontier = sorted(set().union(*(group for group, _ in constraints)) if constraints else set())
    remaining_mines = max(0, observation["mine_count"] - len(flags))
    outside = sorted(unknown.difference(frontier))
    risks: dict[Cell, float] = {}
    if len(frontier) <= 18:
        totals = {cell: 0.0 for cell in frontier}
        total_weight = 0.0
        for values in product((0, 1), repeat=len(frontier)):
            assignment = dict(zip(frontier, values))
            if any(sum(assignment[cell] for cell in group) != count
                   for group, count in constraints):
                continue
            frontier_mines = sum(values)
            outside_mines = remaining_mines - frontier_mines
            if outside_mines < 0 or outside_mines > len(outside):
                continue
            weight = comb(len(outside), outside_mines)
            total_weight += weight
            for cell, value in assignment.items():
                totals[cell] += weight * value
        if total_weight:
            risks.update({cell: totals[cell] / total_weight for cell in frontier})
            if outside:
                expected_outside_mines = 0.0
                for values in product((0, 1), repeat=len(frontier)):
                    assignment = dict(zip(frontier, values))
                    if any(sum(assignment[cell] for cell in group) != count
                           for group, count in constraints):
                        continue
                    outside_mines = remaining_mines - sum(values)
                    if outside_mines < 0 or outside_mines > len(outside):
                        continue
                    expected_outside_mines += comb(len(outside), outside_mines) * outside_mines
                risks.update({
                    cell: expected_outside_mines / (total_weight * len(outside))
                    for cell in outside
                })
                return risks
            return risks

    # Large or inconsistent frontiers use the most conservative local estimate.
    for cell in unknown:
        touching = [
            count / len(group)
            for group, count in constraints if cell in group and len(group)
        ]
        risks[cell] = max(0.0, min(1.0, min(touching) if touching else
                                    remaining_mines / max(1, len(unknown))))
    return risks
