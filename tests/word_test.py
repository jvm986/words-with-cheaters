import unittest
from unittest.mock import MagicMock
from word import Word
from cell import Cell
from tile import Tile


class TestWord(unittest.TestCase):
    def setUp(self):
        """Set up common test variables."""
        self.tile_A = Tile(letter="A", score=1)
        self.tile_B = Tile(letter="B", score=3)
        self.tile_C = Tile(letter="C", score=3)

        self.cell_A = Cell(0, 0, tile=self.tile_A)
        self.cell_B = Cell(0, 1, tile=self.tile_B)
        self.cell_C = Cell(0, 2, tile=self.tile_C)

    def test_word_creation_valid(self):
        """Test that a Word is correctly created with valid cells."""
        word = Word([self.cell_A, self.cell_B, self.cell_C])
        self.assertEqual(str(word), "ABC")

    def test_word_creation_raises_error_with_empty_cell(self):
        """Test that creating a Word with an empty cell raises a ValueError."""
        empty_cell = Cell(0, 0, tile=None)
        with self.assertRaises(ValueError):
            Word([self.cell_A, empty_cell, self.cell_C])

    def test_word_equality(self):
        """Test that two Word objects with the same cells are equal."""
        word1 = Word([self.cell_A, self.cell_B])
        word2 = Word([self.cell_A, self.cell_B])
        self.assertEqual(word1, word2)

    def test_word_inequality(self):
        """Test that two different Word objects are not equal."""
        word1 = Word([self.cell_A, self.cell_B])
        word2 = Word([self.cell_A, self.cell_C])
        self.assertNotEqual(word1, word2)

    def test_word_score_no_multipliers(self):
        """Test score calculation when no multipliers are present."""
        word = Word([self.cell_A, self.cell_B, self.cell_C])
        expected_score = 1 + 3 + 3
        self.assertEqual(word.get_score(), expected_score)

    def test_word_score_with_letter_multipliers(self):
        """Test score calculation with letter multipliers."""
        mock_multiplier_2x = MagicMock()
        mock_multiplier_2x.letter_multiplier.return_value = 2
        mock_multiplier_2x.word_multiplier.return_value = 1

        self.cell_B.multiplier = mock_multiplier_2x

        word = Word([self.cell_A, self.cell_B, self.cell_C])
        expected_score = 1 + (3 * 2) + 3
        self.assertEqual(word.get_score(), expected_score)

    def test_word_score_with_word_multipliers(self):
        """Test score calculation with word multipliers."""
        mock_multiplier_3x = MagicMock()
        mock_multiplier_3x.letter_multiplier.return_value = 1
        mock_multiplier_3x.word_multiplier.return_value = 3

        self.cell_A.multiplier = mock_multiplier_3x

        word = Word([self.cell_A, self.cell_B, self.cell_C])
        base_score = 1 + 3 + 3
        expected_score = base_score * 3
        self.assertEqual(word.get_score(), expected_score)

    def test_word_score_with_mixed_multipliers(self):
        """Test score with both letter and word multipliers."""
        mock_letter_2x = MagicMock()
        mock_letter_2x.letter_multiplier.return_value = 2
        mock_letter_2x.word_multiplier.return_value = 1

        mock_word_2x = MagicMock()
        mock_word_2x.letter_multiplier.return_value = 1
        mock_word_2x.word_multiplier.return_value = 2

        self.cell_A.multiplier = mock_word_2x
        self.cell_B.multiplier = mock_letter_2x

        word = Word([self.cell_A, self.cell_B, self.cell_C])
        base_score = 1 + (3 * 2) + 3
        expected_score = base_score * 2
        self.assertEqual(word.get_score(), expected_score)


if __name__ == "__main__":
    unittest.main()
