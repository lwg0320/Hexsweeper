"""Authoritative rules and the five-operation player interface.

The private board is deliberately kept inside Game. Players receive only the
public observation and a legal-action list.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import random
from typing import Any

RADIUS = 3
MINE_COUNT = 6
BOARD_PRESETS = {
    "small": {"radius": 2, "mine_count": 3},
    "medium": {"radius": 3, "mine_count": 6},
    "large": {"radius": 4, "mine_count": 10},
}
NEIGHBOR_DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1))


class IllegalAction(ValueError):
    """Raised when an action is malformed or is not legal in the current state."""


@dataclass(frozen=True)
class CellView:
    q: int
    r: int
    state: str
    number: int | None = None
    mine: bool | None = None

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"q": self.q, "r": self.r, "state": self.state}
        if self.number is not None:
            result["number"] = self.number
        if self.mine is not None:
            result["mine"] = self.mine
        return result


def board_coordinates(radius: int = RADIUS) -> tuple[tuple[int, int], ...]:
    """Return axial coordinates for a filled hexagon of the requested radius."""
    return tuple(
        (q, r)
        for q in range(-radius, radius + 1)
        for r in range(-radius, radius + 1)
        if max(abs(q), abs(r), abs(q + r)) <= radius
    )


def neighbors(q: int, r: int) -> tuple[tuple[int, int], ...]:
    return tuple((q + dq, r + dr) for dq, dr in NEIGHBOR_DIRECTIONS)


class Game:
    """A single episode. Only these five methods form the player interface."""

    def __init__(self, radius: int = RADIUS, mine_count: int = MINE_COUNT):
        if radius < 1:
            raise ValueError("radius must be at least 1")
        if not 1 <= mine_count < len(board_coordinates(radius)):
            raise ValueError("mine_count must fit on the board")
        self.radius = radius
        self.mine_count = mine_count
        self.reset(0)

    def reset(self, seed: int | str) -> dict[str, Any]:
        self._seed = str(seed)
        self._cells = board_coordinates(self.radius)
        self._cell_set = set(self._cells)
        self._mines: set[tuple[int, int]] | None = None
        self._numbers: dict[tuple[int, int], int] = {}
        self._revealed: set[tuple[int, int]] = set()
        self._flags: set[tuple[int, int]] = set()
        self._exploded: tuple[int, int] | None = None
        self._terminal_reason: str | None = None
        self._safe_first_reveal: tuple[int, int] | None = None
        return self.observe("player")

    def observe(self, player_id: str = "player") -> dict[str, Any]:
        """Return only visible board data. The seed and mine map are never sent."""
        if self._terminal_reason is None:
            views = [
                CellView(
                    q=q,
                    r=r,
                    state=("revealed" if (q, r) in self._revealed else
                           "flagged" if (q, r) in self._flags else "hidden"),
                    number=self._numbers[(q, r)] if (q, r) in self._revealed else None,
                    mine=None,
                ).as_dict()
                for q, r in self._cells
            ]
        else:
            views = []
            for q, r in self._cells:
                is_revealed = (q, r) in self._revealed
                views.append(
                    CellView(
                        q=q,
                        r=r,
                        state=("revealed" if is_revealed else
                               "flagged" if (q, r) in self._flags else "hidden"),
                        number=self._numbers[(q, r)] if is_revealed else None,
                        mine=((q, r) in (self._mines or set())),
                    ).as_dict()
                )
        result: dict[str, Any] = {
            "radius": self.radius,
            "mine_count": self.mine_count,
            "cells": views,
            "revealed_safe": len(self._revealed),
            "flag_count": len(self._flags),
            "first_reveal": (
                {"q": self._safe_first_reveal[0], "r": self._safe_first_reveal[1]}
                if self._safe_first_reveal is not None else None
            ),
        }
        return result

    def legal_actions(self, player_id: str = "player") -> list[dict[str, Any]]:
        """List actions from visible status only; never inspect mine placement."""
        if self._terminal_reason is not None:
            return []
        actions: list[dict[str, Any]] = []
        for q, r in self._cells:
            cell = (q, r)
            if cell in self._revealed:
                continue
            actions.append({"type": "flag", "q": q, "r": r})
            if cell not in self._flags:
                actions.append({"type": "reveal", "q": q, "r": r})
        return actions

    def step(self, player_id: str, action: dict[str, Any]) -> dict[str, Any]:
        """Validate one action, apply it, and return the visible transition."""
        if not isinstance(action, dict) or set(action) != {"type", "q", "r"}:
            raise IllegalAction("action must contain exactly type, q, and r")
        kind, q, r = action["type"], action["q"], action["r"]
        if kind not in ("reveal", "flag"):
            raise IllegalAction("type must be reveal or flag")
        if isinstance(q, bool) or not isinstance(q, int):
            raise IllegalAction("q must be an integer")
        if isinstance(r, bool) or not isinstance(r, int):
            raise IllegalAction("r must be an integer")
        if action not in self.legal_actions(player_id):
            raise IllegalAction("action is not legal in the current position")

        event: dict[str, Any] = {"action": dict(action), "changed": []}
        cell = (q, r)
        if kind == "flag":
            if cell in self._flags:
                self._flags.remove(cell)
                event["result"] = "unflagged"
            else:
                self._flags.add(cell)
                event["result"] = "flagged"
        else:
            if self._mines is None:
                self._place_mines_safely(cell)
                self._safe_first_reveal = cell
            if cell in self._mines:
                self._exploded = cell
                self._terminal_reason = "mine_revealed"
                event["result"] = "mine"
            else:
                newly_revealed = self._reveal_region(cell)
                event["changed"] = [{"q": x, "r": y} for x, y in newly_revealed]
                event["result"] = "revealed"
                if len(self._revealed) == len(self._cells) - self.mine_count:
                    self._terminal_reason = "all_safe_cells_revealed"

        return {
            "event": event,
            "observation": self.observe(player_id),
            "legal_actions": self.legal_actions(player_id),
            "outcome": self.outcome(),
        }

    def outcome(self) -> dict[str, Any]:
        """Return the episode status and score without exposing hidden cells."""
        score = len(self._revealed)
        if self._terminal_reason is None:
            return {"terminal": False, "reason": None, "score": score}
        won = self._terminal_reason == "all_safe_cells_revealed"
        return {
            "terminal": True,
            "reason": self._terminal_reason,
            "result": "win" if won else "loss",
            "score": score,
            "safe_cells": len(self._cells) - self.mine_count,
            "detail": (
                "mine at " + str(self._exploded[0]) + "," + str(self._exploded[1])
                if self._exploded is not None else None
            ),
        }

    def _place_mines_safely(self, first_cell: tuple[int, int]) -> None:
        """Place mines deterministically from the episode seed, excluding first click."""
        candidates = [cell for cell in self._cells if cell != first_cell]
        # Include the first coordinate in the local seed so each opening has a
        # reproducible board, while keeping the episode seed out of observations.
        opening_seed = self._seed + ":" + str(first_cell[0]) + ":" + str(first_cell[1])
        rng = random.Random(opening_seed)
        self._mines = set(rng.sample(candidates, self.mine_count))
        self._numbers = {
            cell: sum(1 for neighbor in neighbors(*cell) if neighbor in self._mines)
            for cell in self._cells
        }

    def _reveal_region(self, start: tuple[int, int]) -> list[tuple[int, int]]:
        """Reveal one safe cell and its connected zero region, as in Minesweeper."""
        changed: list[tuple[int, int]] = []
        queue = deque([start])
        queued = {start}
        while queue:
            cell = queue.popleft()
            if cell in self._revealed or cell in self._flags or cell in (self._mines or set()):
                continue
            self._revealed.add(cell)
            changed.append(cell)
            if self._numbers[cell] == 0:
                for neighbor in neighbors(*cell):
                    if neighbor in self._cell_set and neighbor not in queued:
                        queued.add(neighbor)
                        queue.append(neighbor)
        return changed
