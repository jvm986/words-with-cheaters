import argparse
import logging
import os
from parser import Parser

from board import Board
from dictionary import Dictionary
from game import Game
from rack import Rack

DICTIONARY_FILE = "dictionary.txt"
SCREENSHOT_DIR = "screenshots"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

parser = Parser()
dictionary = Dictionary(DICTIONARY_FILE)


def process(screenshot_name, model=None, solve=False, reparse=False):
    logging.info(f"Processing screenshot: {screenshot_name}")

    screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)
    board_path = os.path.join(screenshot_path, "board.json")
    rack_path = os.path.join(screenshot_path, "rack.json")

    if not os.path.exists(board_path) or not os.path.exists(rack_path) or reparse:
        logging.info(f"Parsing screenshot: {screenshot_name} with model: {model or 'default'}")
        board, rack = parser.parse_screenshot(os.path.join(screenshot_path, "screenshot.png"), model)

        board.save_board_to_file(board_path)
        rack.save_rack_to_file(rack_path)

    board = Board.load_board_from_file(board_path)
    rack = Rack.load_rack_from_file(rack_path)
    board.save_board_to_file(board_path)
    rack.save_rack_to_file(rack_path)

    game = Game(dictionary, board, rack)

    try:
        game.validate_board()
    except ValueError as e:
        board.print_letters()
        board.print_scores()
        board.print_mutlipliers()
        rack.print_letters()
        rack.print_scores()
        logging.error(f"Board validation failed: {e}")
        return

    if solve:
        logging.info("Solving board")
        scored_possible_words = game.get_scored_possible_words()
        print(scored_possible_words[:5])
        for word in scored_possible_words[0][0]:
            board.add_word(word)
        board.print_letters()
        rack.print_letters()


def main():
    parser = argparse.ArgumentParser(description="Words With Friends Solver")
    parser.add_argument(
        "-s",
        "--screenshot",
        help="Name of the screenshot to process (optional, processes all if not specified)",
    )
    parser.add_argument(
        "-m",
        "--model",
        help="Name to the tesseract model",
    )
    parser.add_argument("--solve", action="store_true", help="Enable solving mode")
    parser.add_argument("--reparse", action="store_true", help="Reparse the screenshot(s)")

    args = parser.parse_args()

    if args.screenshot:
        process(args.screenshot, args.model, args.solve, args.reparse)
    else:
        for screenshot_name in os.listdir(SCREENSHOT_DIR):
            process(screenshot_name, args.model, args.solve)


if __name__ == "__main__":
    main()
