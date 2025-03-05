import unittest
from board import Board, Direction

BOARD_DIMENSION = 5
BOARD_CENTER = 2
MULTIPLIERS_FILE = "tests/fixtures/multipliers.csv"


class TestBoard(unittest.TestCase):
    def setUp(self):
        self.board = Board(
            board_dimension=BOARD_DIMENSION, multipliers_file=MULTIPLIERS_FILE
        )

    def test_board_initialization(self):
        self.assertTrue(self.board.board_is_empty())

    def test_get_cell(self):
        self.assertEqual(self.board.get_cell(0, 0), "-")

    def test_get_words(self):
        self.board.add_word("hi", BOARD_CENTER, BOARD_CENTER, Direction.HORIZONTAL)
        self.assertEqual(self.board.get_words(), [("hi", (2, 2), Direction.HORIZONTAL)])

    def test_get_series(self):
        self.board.add_word("hi", BOARD_CENTER, BOARD_CENTER, Direction.VERTICAL)
        self.assertEqual(
            self.board.get_series(1, 2, 2, Direction.VERTICAL), ["-", "h", "i", "-"]
        )
        self.assertEqual(
            self.board.get_series(2, 1, 2, Direction.HORIZONTAL), ["-", "h", "-"]
        )

    def test_word_is_placable(self):
        self.board.add_word("hi", BOARD_CENTER, BOARD_CENTER, Direction.HORIZONTAL)
        self.assertTrue(self.board.word_is_placable("ho", 2, 2, Direction.VERTICAL))
        self.assertFalse(self.board.word_is_placable("ho", 2, 2, Direction.HORIZONTAL))

    def test_add_word(self):
        self.board.add_word("hi", BOARD_CENTER, BOARD_CENTER, Direction.HORIZONTAL)
        self.assertEqual(self.board.get_cell(2, 2), "h")
        self.assertEqual(self.board.get_cell(2, 3), "i")

    def test_get_word_score(self):
        self.board.add_word("hi", BOARD_CENTER, BOARD_CENTER, Direction.HORIZONTAL)
        self.assertEqual(
            self.board.get_word_score(
                ["i"], "hi", BOARD_CENTER, BOARD_CENTER, Direction.VERTICAL
            ),
            5,
        )


if __name__ == "__main__":
    unittest.main()
