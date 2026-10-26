import unittest

from hex_minesweeper.game import Game, IllegalAction, board_coordinates, neighbors


def fixed_layout(game, mines):
    """Install a controlled mine map for rule tests."""
    game._mines = set(mines)
    game._numbers = {
        cell: sum(1 for adjacent in neighbors(*cell) if adjacent in game._mines)
        for cell in game._cells
    }


class GeometryTests(unittest.TestCase):
    def test_radius_three_board_has_thirty_seven_hexes(self):
        self.assertEqual(len(board_coordinates(3)), 37)

    def test_interior_hex_has_six_neighbors(self):
        valid = set(board_coordinates(3))
        self.assertEqual(len([cell for cell in neighbors(0, 0) if cell in valid]), 6)


class GameRulesTests(unittest.TestCase):
    def test_reset_is_hidden_and_has_no_seed_or_mine_map(self):
        game = Game()
        game.reset(73)
        view = game.observe("player")
        self.assertNotIn("seed", view)
        self.assertNotIn("mines", view)
        self.assertTrue(all("mine" not in cell for cell in view["cells"]))
        self.assertEqual(len(game.legal_actions("player")), 37 * 2)

    def test_first_reveal_is_safe_and_seeded_opening_is_reproducible(self):
        first = Game()
        second = Game()
        first.reset(2026)
        second.reset(2026)
        action = {"type": "reveal", "q": 0, "r": 0}
        left = first.step("player", action)
        right = second.step("player", action)
        self.assertNotIn((0, 0), first._mines)
        self.assertEqual(left["observation"], right["observation"])
        self.assertEqual(left["event"]["result"], "revealed")

    def test_seed_and_first_coordinate_define_the_fixed_layout(self):
        left = Game()
        right = Game()
        left.reset("case-a")
        right.reset("case-a")
        left.step("player", {"type": "reveal", "q": 0, "r": 0})
        right.step("player", {"type": "reveal", "q": 1, "r": 0})
        # The opening is safe in both boards and the deterministic generator
        # keys the resulting layout to the same seed and different opening.
        self.assertNotEqual(left._mines, right._mines)

    def test_zero_reveal_expands_only_safe_cells(self):
        game = Game(radius=2, mine_count=1)
        game.reset(1)
        fixed_layout(game, {(2, 0)})
        transition = game.step("player", {"type": "reveal", "q": -2, "r": 0})
        changed = {(item["q"], item["r"]) for item in transition["event"]["changed"]}
        self.assertTrue(changed)
        self.assertNotIn((2, 0), changed)
        self.assertTrue(all(cell not in game._mines for cell in changed))
        self.assertGreater(len(changed), 1)

    def test_flags_toggle_and_flagged_cells_cannot_be_revealed(self):
        game = Game()
        game.reset(11)
        target = {"q": -3, "r": 0}
        game.step("player", {"type": "flag", **target})
        self.assertNotIn({"type": "reveal", **target}, game.legal_actions("player"))
        self.assertIn({"type": "flag", **target}, game.legal_actions("player"))
        game.step("player", {"type": "flag", **target})
        self.assertIn({"type": "reveal", **target}, game.legal_actions("player"))
        self.assertEqual(game.observe()["flag_count"], 0)

    def test_legal_actions_do_not_depend_on_hidden_mine_positions(self):
        first = Game()
        second = Game()
        for game, mines in (
            (first, {(1, 0), (2, 0), (-2, 1), (0, 2), (-1, -2), (2, -2)}),
            (second, {(0, 1), (2, 0), (-2, 1), (0, 2), (-1, -2), (2, -2)}),
        ):
            game.reset(4)
            fixed_layout(game, mines)
            game.step("player", {"type": "reveal", "q": 0, "r": 0})
        self.assertEqual(first.legal_actions(), second.legal_actions())

    def test_mine_reveal_loses_and_discloses_board_only_after_terminal(self):
        game = Game(radius=2, mine_count=1)
        game.reset(2)
        fixed_layout(game, {(2, 0)})
        game.step("player", {"type": "reveal", "q": 1, "r": 0})
        self.assertTrue(all("mine" not in cell for cell in game.observe()["cells"]))
        result = game.step("player", {"type": "reveal", "q": 2, "r": 0})
        self.assertEqual(result["outcome"]["result"], "loss")
        self.assertEqual(result["outcome"]["reason"], "mine_revealed")
        self.assertEqual(result["outcome"]["detail"], "mine at 2,0")
        self.assertTrue(all("mine" in cell for cell in result["observation"]["cells"]))
        self.assertEqual(game.legal_actions(), [])

    def test_all_safe_cells_is_a_win_without_flagging_mines(self):
        game = Game(radius=2, mine_count=1)
        game.reset(17)
        fixed_layout(game, {(2, 0)})
        for cell in game._cells:
            if cell not in game._mines and cell not in game._revealed:
                game.step("player", {"type": "reveal", "q": cell[0], "r": cell[1]})
        self.assertEqual(game.outcome()["result"], "win")
        self.assertEqual(game.outcome()["reason"], "all_safe_cells_revealed")

    def test_invalid_action_is_rejected_without_mutating_board(self):
        game = Game()
        game.reset(0)
        before = game.observe()
        for action in (
            {"type": "reveal", "q": 8, "r": 8},
            {"type": "reveal", "q": 0, "r": 0, "mine": True},
            {"type": "chord", "q": 0, "r": 0},
            {"type": "flag", "q": True, "r": 0},
        ):
            with self.subTest(action=action):
                with self.assertRaises(IllegalAction):
                    game.step("player", action)
        self.assertEqual(game.observe(), before)


if __name__ == "__main__":
    unittest.main()
