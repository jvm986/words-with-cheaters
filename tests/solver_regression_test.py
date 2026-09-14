import unittest

from board import Board, Direction
from cell import Cell, Multiplier
from dictionary import Dictionary
from game import Game
from rack import Rack
from tile import Tile


def game_for(words, rack, rows=5, cols=5):
    dictionary = Dictionary()
    for word in words:
        dictionary.insert(word)
    board = Board([[Cell(r, c) for c in range(cols)] for r in range(rows)])
    return Game(dictionary, board, Rack([Tile(letter, 0 if letter == "?" else 1) for letter in rack]))


def placements(game):
    return {
        tuple((cell.row, cell.col, cell.tile.letter, cell.tile.score) for cell in word.cells)
        for word in game.get_possible_words()
    }


class SolverRegressionTests(unittest.TestCase):
    def test_duplicate_letters(self):
        game = game_for(["EEL"], "EEL")
        words = game.find_words_for_series(game.board.get_empty_board_series(3), set())
        self.assertEqual([str(word) for word in words], ["EEL"])
        self.assertEqual(game.rack.get_letters(), list("EEL"))

    def test_insufficient_duplicate_letters(self):
        game = game_for(["EEL"], "ELT")
        self.assertEqual(game.get_scored_possible_words(), [])

    def test_final_letter_blank(self):
        game = game_for(["CAT"], "CA?")
        words = game.find_words_for_series(game.board.get_empty_board_series(3), set())
        self.assertEqual([str(word) for word in words], ["CAT"])
        self.assertEqual([cell.tile.score for cell in words[0].cells], [1, 1, 0])

    def test_two_blanks(self):
        game = game_for(["CAT"], "C??")
        words = game.find_words_for_series(game.board.get_empty_board_series(3), set())
        self.assertEqual([str(word) for word in words], ["CAT"])
        self.assertEqual([cell.tile.score for cell in words[0].cells], [1, 0, 0])

    def test_blank_assignment_changes_ranking(self):
        game = game_for(["AA"], "A?")
        game.board.cells[2][3].multiplier = Multiplier.TL
        words = game.find_words_for_series(game.board.get_empty_board_series(2), set())
        self.assertEqual({tuple(c.tile.score for c in w.cells) for w in words}, {(0, 1), (1, 0)})
        scored = game.get_scored_possible_words()
        self.assertEqual(scored[0][1], 3)
        self.assertEqual(scored[-1][1], 1)

    def test_complete_opening_moves_and_scores(self):
        game = game_for(["CAT"], "CAT")
        expected = set()
        for start in range(3):
            expected.add(tuple((2, start + i, letter, 1) for i, letter in enumerate("CAT")))
            expected.add(tuple((start + i, 2, letter, 1) for i, letter in enumerate("CAT")))
        self.assertEqual(placements(game), expected)
        self.assertEqual([score for _, score, _ in game.get_scored_possible_words()], [3] * 6)

    def test_vertical_move_with_occupied_left_neighbor(self):
        game = game_for(["AC", "CAT"], "C")
        game.board.cells[1][1].tile = Tile("A", 1)
        game.board.cells[2][2].tile = Tile("A", 1)
        game.board.cells[3][2].tile = Tile("T", 1)
        self.assertIn(((1, 2, "C", 1), (2, 2, "A", 1), (3, 2, "T", 1)), placements(game))
        self.assertTrue(
            any(
                {str(w) for w in words} == {"AC", "CAT"} and score == 5
                for words, score, _ in game.get_scored_possible_words()
            )
        )

    def test_complete_moves_around_existing_tile(self):
        game = game_for(["AT", "TA"], "T", 3, 3)
        game.board.cells[1][1].tile = Tile("A", 1)
        scored = game.get_scored_possible_words()
        actual = {tuple((c.row, c.col, c.tile.letter) for c in words[0].cells) for words, _, _ in scored}
        self.assertEqual(
            actual,
            {
                ((1, 0, "T"), (1, 1, "A")),
                ((1, 1, "A"), (1, 2, "T")),
                ((0, 1, "T"), (1, 1, "A")),
                ((1, 1, "A"), (2, 1, "T")),
            },
        )
        self.assertEqual([score for _, score, _ in scored], [2] * 4)

    def test_old_premiums_not_reused(self):
        for multiplier in Multiplier:
            with self.subTest(multiplier=multiplier):
                game = game_for(["AT"], "T")
                game.board.cells[2][2] = Cell(2, 2, Tile("A", 1), multiplier)
                self.assertEqual([score for _, score, _ in game.get_scored_possible_words()], [2, 2])
                self.assertEqual(game.board.cells[2][2].multiplier, multiplier)

    def test_new_premium_applies_to_both_crossing_words(self):
        game = game_for(["AT"], "T")
        game.board.cells[2][1].tile = Tile("A", 1)
        game.board.cells[1][2].tile = Tile("A", 1)
        game.board.cells[2][2].multiplier = Multiplier.DW
        results = game.get_scored_possible_words()
        self.assertTrue(any(len(words) == 2 and score == 8 and count == 1 for words, score, count in results))
        self.assertIsNone(game.board.cells[2][2].tile)

    def test_existing_blank_stays_zero(self):
        game = game_for(["AT"], "T")
        game.board.cells[2][2] = Cell(2, 2, Tile("A", 0), Multiplier.TW)
        self.assertEqual([score for _, score, _ in game.get_scored_possible_words()], [1, 1])

    def test_seven_tile_bonus(self):
        game = game_for(["LETTERS"], "LETTERS", 15, 15)
        self.assertEqual({score for _, score, _ in game.get_scored_possible_words()}, {47})

    def test_rectangular_board_series(self):
        wide = game_for(["ABCDE"], "ABCDE", 3, 5)
        self.assertEqual(len(wide.board.get_series(1, 0, 5, Direction.HORIZONTAL)), 5)
        tall = game_for(["ABCDE"], "ABCDE", 5, 3)
        self.assertEqual(len(tall.board.get_series(0, 1, 5, Direction.VERTICAL)), 5)
        self.assertEqual(tall.board.get_series(4, 1, 2, Direction.VERTICAL), [])

    def test_invalid_crossword_is_rejected(self):
        game = game_for(["CAT"], "C")
        game.board.cells[1][1].tile = Tile("A", 1)
        game.board.cells[2][2].tile = Tile("A", 1)
        game.board.cells[3][2].tile = Tile("T", 1)
        self.assertFalse(
            any(
                any(str(word) == "CAT" and word.cells[0].row == 1 and word.cells[0].col == 2 for word in words)
                for words, _, _ in game.get_scored_possible_words()
            )
        )

    def test_new_premium_is_not_reused_on_following_turn(self):
        game = game_for(["AT", "ATE"], "T")
        game.board.cells[2][1].tile = Tile("A", 1)
        game.board.cells[2][2].multiplier = Multiplier.TW
        opening = next(
            word
            for word in game.get_possible_words()
            if str(word) == "AT" and word.cells[0].row == 2 and word.cells[0].col == 1
        )
        game.board.add_word(opening)
        game.rack = Rack([Tile("E", 1)])
        results = game.get_scored_possible_words()
        extension = next(
            score for words, score, _ in results if any(str(word) == "ATE" and word.cells[0].row == 2 for word in words)
        )
        self.assertEqual(extension, 3)
