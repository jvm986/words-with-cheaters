import logging
from board import Board
from dictionary import Dictionary
from game import Game
import sys
import os

BOARD_DIMENSION = 15
BOARD_FILE = None

if len(sys.argv) > 1:
    board_file_arg = sys.argv[1]
    if os.path.exists(board_file_arg):
        BOARD_FILE = board_file_arg

MULTIPLIERS_FILE = "multipliers.csv"
LETTER_SCORES_FILE = "letter_scores.csv"
DICTIONARY_FILE = "dictionary.txt"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    board = Board(
        BOARD_DIMENSION, multipliers_file=MULTIPLIERS_FILE, board_file=BOARD_FILE
    )

    dictionary = Dictionary(DICTIONARY_FILE)

    game = Game(dictionary, board)
    if not game.is_board_valid():
        raise ValueError("Board is not valid")

    game.set_rack(
        [
            "o",
            "i",
            "u",
            "e",
            "e",
            "s",
            "a",
        ]
    )

    words = game.get_scored_possible_words()
    logger.info(f"Adding: {words[0][0]} for {words[0][3]} points")
    board.add_word(words[0][0], words[0][1][0], words[0][1][1], words[0][2])
    board.print_board()
    board.save_board_to_file(BOARD_FILE)
