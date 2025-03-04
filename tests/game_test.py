import unittest

from board import Board, Direction
from dictionary import Dictionary
from game import Game

BOARD_DIMENSION = 5
BOARD_CENTER = 2
DICTIONARY_FILE = "dictionary.txt"


class TestGame(unittest.TestCase):
    def setUp(self):
        self.dictionary = Dictionary()
        self.dictionary.load_from_file(DICTIONARY_FILE)
        self.board = Board(BOARD_DIMENSION)
        self.game = Game(self.dictionary, self.board)

    def test_game_initialization(self):
        self.assertEqual(self.game.rack, [])

    def test_find_words_for_range(self):
        self.board.add_word("hi", BOARD_CENTER, BOARD_CENTER, Direction.VERTICAL)
        self.game.set_rack(["W", "O"])
        r = self.board.get_range(2, 1, 2, Direction.HORIZONTAL)
        valid_words = self.game.find_words_for_range(r)
        self.assertEqual(valid_words, {"who"})

    def test_get_scored_possible_words(self):
        self.board.add_word("hi", BOARD_CENTER, BOARD_CENTER, Direction.VERTICAL)
        self.game.set_rack(["o"])
        words = self.game.get_scored_possible_words()
        self.assertIn(
            ("ho", (2, 2), Direction.HORIZONTAL, 5),
            words,
        )

    def test_get_scored_possible_words_with_blank(self):
        self.board.add_word("hi", BOARD_CENTER, BOARD_CENTER, Direction.VERTICAL)
        self.game.set_rack(["o", "?"])
        words = self.game.get_scored_possible_words()
        self.assertIn(
            ("thio", (1, 2), Direction.VERTICAL, 6),
            words,
        )
