import unittest
from unittest.mock import MagicMock
from game import Game
from board import Board, Direction
from cell import Cell
from dictionary import Dictionary
from rack import Rack
from tile import Tile
from word import Word


class TestGame(unittest.TestCase):
    def setUp(self):
        """Set up a game with a mock dictionary, board, and rack."""
        self.dictionary = MagicMock()
        self.dictionary.search.return_value = True
        self.dictionary.search_with_pattern.return_value = ["CAT", "BAT"]

        self.tile_A = Tile(letter="A", score=1)
        self.tile_B = Tile(letter="B", score=3)
        self.tile_C = Tile(letter="C", score=3)
        self.tile_T = Tile(letter="T", score=1)

        self.cell_C = Cell(row=7, col=7, tile=self.tile_C)
        self.cell_A = Cell(row=7, col=8, tile=self.tile_A)
        self.cell_T = Cell(row=7, col=9, tile=self.tile_T)

        self.empty_cells = [[Cell(row=r, col=c) for c in range(15)] for r in range(15)]
        self.board = Board(self.empty_cells)

        self.rack = Rack([self.tile_T])

        self.game = Game(dictionary=self.dictionary, board=self.board, rack=self.rack)

    def test_game_initialization(self):
        """Test that the game initializes correctly."""
        self.assertEqual(self.game.board, self.board)
        self.assertEqual(self.game.rack, self.rack)
        self.assertEqual(self.game.dictionary, self.dictionary)

    def test_get_possible_words_on_empty_board(self):
        """Test that possible words are found when the board is empty."""
        self.board.is_board_empty = MagicMock(return_value=True)
        self.board.get_empty_board_series = MagicMock(return_value=[self.cell_C, self.cell_A, self.cell_T])

        possible_words = self.game.get_possible_words()
        self.assertTrue(any(str(word) == "CAT" for word in possible_words))

    def test_get_possible_words_on_non_empty_board(self):
        """Test that words are found when the board has existing tiles."""
        self.board.is_board_empty = MagicMock(return_value=False)
        self.board.get_series = MagicMock(return_value=[self.cell_C, self.cell_A, self.cell_T])

        possible_words = self.game.get_possible_words()
        self.assertTrue(any(str(word) == "CAT" for word in possible_words))

    def test_get_scored_possible_words(self):
        """Test that scored possible words are returned correctly."""
        self.game.get_possible_words = MagicMock(return_value=[Word([self.cell_C, self.cell_A, self.cell_T])])
        self.board.get_board_words = MagicMock(side_effect=[[], [Word([self.cell_C, self.cell_A, self.cell_T])]])
        self.board.clone = MagicMock(return_value=self.board)
        self.board.add_word = MagicMock()
        self.game.validate_board = MagicMock()

        scored_words = self.game.get_scored_possible_words()
        self.assertGreater(len(scored_words), 0)
        self.assertEqual(
            scored_words[0][1],
            self.tile_C.score + self.tile_A.score + self.tile_T.score,
        )

    def test_find_words_for_series(self):
        """Test that words can be found given a series of cells."""
        series = [self.cell_C, self.cell_A, self.cell_T]

        valid_words = self.game.find_words_for_series(series)
        self.assertTrue(any(str(word) == "CAT" for word in valid_words))

    def test_validate_board(self):
        """Test board validation against the dictionary."""
        word = Word([self.cell_C, self.cell_A, self.cell_T])
        self.board.get_board_words = MagicMock(return_value=[word])
        self.dictionary.search = MagicMock(return_value=True)

        try:
            self.game.validate_board()
        except ValueError:
            self.fail("validate_board() raised ValueError unexpectedly")

    def test_validate_board_with_invalid_word(self):
        """Test board validation raises an error when a word is invalid."""
        word = Word([self.cell_C, self.cell_A, self.cell_T])
        self.board.get_board_words = MagicMock(return_value=[word])
        self.dictionary.search = MagicMock(return_value=False)

        with self.assertRaises(ValueError):
            self.game.validate_board()


if __name__ == "__main__":
    unittest.main()
