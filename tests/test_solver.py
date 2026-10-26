import unittest

from hex_minesweeper.game import Game, board_coordinates
from hex_minesweeper.solver import choose_solver_action


class SolverTests(unittest.TestCase):
    def test_solver_reveals_a_cell_forced_safe_by_zero_clue(self):
        board = set(board_coordinates(2))
        cells = [
            {"q": q, "r": r, "state": "hidden"}
            for q, r in sorted(board)
        ]
        center = next(cell for cell in cells if cell["q"] == 0 and cell["r"] == 0)
        center["state"] = "revealed"
        center["number"] = 0
        legal = [
            {"type": kind, "q": q, "r": r}
            for q, r in sorted(board)
            for kind in ("reveal", "flag")
        ]
        action = choose_solver_action(
            {"cells": cells, "mine_count": 1}, legal
        )
        self.assertEqual(action["type"], "reveal")
        self.assertNotEqual((action["q"], action["r"]), (0, 0))

    def test_solver_uses_only_interface_data(self):
        game = Game()
        game.reset(3)
        action = choose_solver_action(game.observe(), game.legal_actions())
        self.assertIn(action, game.legal_actions())
        self.assertEqual(action["type"], "reveal")


if __name__ == "__main__":
    unittest.main()
