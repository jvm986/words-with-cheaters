import time
import unittest

from board import Board
from dictionary import Dictionary
from game import Game

BOARD_DIMENSION = 15
BOARD_CENTER = 7
DICTIONARY_FILE = "dictionary.txt"
BOARD_FILE = "tests/fixtures/benchmark_board.csv"
MULTIPLIERS_FILE = "tests/fixtures/benchmark_multipliers.csv"


class TestGameBenchmark(unittest.TestCase):
    def setUp(self):
        self.dictionary = Dictionary()
        self.dictionary.load_from_file(DICTIONARY_FILE)
        self.board = Board(
            BOARD_DIMENSION,
            board_file=BOARD_FILE,
            multipliers_file=MULTIPLIERS_FILE,
        )
        self.game = Game(self.dictionary, self.board)

    def test_get_scored_possible_words(self):
        self.game.set_rack(["a", "b", "c", "d", "e", "f"])

        start_time = time.time()
        self.game.get_scored_possible_words()
        end_time = time.time()

        elapsed_time = end_time - start_time
        print(f"Benchmark: get_scored_possible_words took {elapsed_time:.6f} seconds")

        with open("tests/benchmark_result", "w") as file:
            file.write(f"{elapsed_time:.6f}")
