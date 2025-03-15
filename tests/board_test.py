import unittest
import json
import os
from board import Board, BoardEncoder, Direction
from cell import Cell, Multiplier
from tile import Tile
from word import Word


class TestBoard(unittest.TestCase):
    def setUp(self):
        """Set up a standard test board."""
        self.tile_A = Tile(letter="A", score=1)
        self.tile_B = Tile(letter="B", score=3)
        self.tile_C = Tile(letter="C", score=3)

        self.cell_A = Cell(row=7, col=7, tile=self.tile_A)
        self.cell_B = Cell(row=7, col=8, tile=self.tile_B)
        self.cell_C = Cell(row=7, col=9, tile=self.tile_C)

        self.empty_cells = [[Cell(row=r, col=c) for c in range(15)] for r in range(15)]
        self.board = Board(self.empty_cells)

    def test_board_creation(self):
        """Test board initialization with correct dimensions."""
        self.assertEqual(len(self.board.cells), 15)
        self.assertEqual(len(self.board.cells[0]), 15)

    def test_board_is_empty(self):
        """Test that an empty board is correctly identified."""
        self.assertTrue(self.board.board_is_empty())

        self.board.cells[7][7] = self.cell_A
        self.assertFalse(self.board.board_is_empty())

    def test_get_cell(self):
        """Test retrieving a specific cell."""
        cell = self.board.get_cell(7, 7)
        self.assertEqual(cell.row, 7)
        self.assertEqual(cell.col, 7)
        self.assertIsNone(cell.tile)

    def test_get_row(self):
        """Test retrieving a row."""
        row = self.board.get_row(7)
        self.assertEqual(len(row), 15)
        self.assertIsInstance(row[0], Cell)

    def test_get_col(self):
        """Test retrieving a column."""
        col = self.board.get_col(7)
        self.assertEqual(len(col), 15)
        self.assertIsInstance(col[0], Cell)

    def test_get_words_from_series(self):
        """Test extracting words from a row or column."""
        self.board.cells[7][7] = self.cell_A
        self.board.cells[7][8] = self.cell_B
        self.board.cells[7][9] = self.cell_C

        words = self.board.get_words_from_series(self.board.get_row(7))
        self.assertEqual(len(words), 1)
        self.assertEqual(str(words[0]), "ABC")

    def test_get_board_words(self):
        """Test retrieving all words from the board."""
        self.board.cells[7][7] = self.cell_A
        self.board.cells[7][8] = self.cell_B
        self.board.cells[7][9] = self.cell_C

        words = self.board.get_board_words()
        self.assertEqual(len(words), 1)
        self.assertEqual(str(words[0]), "ABC")

    def test_word_intersects_center(self):
        """Test if a word intersects the center of the board."""
        word = Word([self.cell_A, self.cell_B, self.cell_C])
        self.assertTrue(self.board.word_intersects_center(word))

        off_center_word = Word([Cell(row=0, col=0, tile=self.tile_A)])
        self.assertFalse(self.board.word_intersects_center(off_center_word))

    def test_word_is_placable(self):
        """Test if a word can be placed on the board."""
        word = Word([self.cell_A, self.cell_B, self.cell_C])
        self.assertTrue(self.board.word_is_placable(word))

        conflicting_cell = Cell(row=7, col=7, tile=Tile("X", 8))
        self.board.cells[7][7] = conflicting_cell

        with self.assertRaises(ValueError):
            self.board.word_is_placable(word)

    def test_add_word(self):
        """Test placing a word on the board."""
        word = Word([self.cell_A, self.cell_B, self.cell_C])
        self.board.add_word(word)

        self.assertEqual(self.board.cells[7][7].tile.letter, "A")
        self.assertEqual(self.board.cells[7][8].tile.letter, "B")
        self.assertEqual(self.board.cells[7][9].tile.letter, "C")

    def test_save_and_load_board(self):
        """Test saving and loading a board from a file."""
        file_path = "test_board.json"
        self.board.save_board_to_file(file_path)

        loaded_board = Board.load_board_from_file(file_path)

        self.assertEqual(len(loaded_board.cells), 15)
        self.assertEqual(len(loaded_board.cells[0]), 15)

        os.remove(file_path)

    def test_board_encoder(self):
        """Test board JSON encoding."""
        encoded_board = json.dumps(self.board.cells, cls=BoardEncoder)
        decoded_board = json.loads(encoded_board)

        self.assertEqual(len(decoded_board), 15)
        self.assertEqual(len(decoded_board[0]), 15)
        self.assertIsNone(decoded_board[7][7]["tile"])

    def test_cell_touches_tile(self):
        """Test if a cell touches a tile."""
        self.board.cells[7][7] = self.cell_A
        self.assertTrue(self.board.cell_touches_tile(7, 8))

        self.assertFalse(self.board.cell_touches_tile(0, 0))


if __name__ == "__main__":
    unittest.main()
