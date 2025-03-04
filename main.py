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
RACK = None
if len(sys.argv) > 2:
    RACK = list(sys.argv[2])

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

    game.set_rack(RACK)

    words = game.get_scored_possible_words()
    logger.info([{word[0]: word[3]} for word in words])

    for i, word in enumerate(words):
        logger.info(f"{word[0]}: {word[3]} points")
        board.add_word(word[0], word[1][0], word[1][1], word[2])
        board.print_board()
        logger.info(f"Added: {word[0]} for {word[3]} points")
        user_input = input(
            "Do you want to save the board to file? (y/n), type 'c' to cancel: "
        )
        if user_input.lower() == "y":
            board.save_board_to_file(BOARD_FILE)
            logger.info("Board saved to file.")
            break
        elif user_input.lower() == "c":
            logger.info("Cancelled.")
            break
        else:
            board.load_board_from_file(BOARD_FILE)
