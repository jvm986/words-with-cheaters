import copy
from venv import logger
from board import Board, Direction
from dictionary import Dictionary


class Game:
    def __init__(self, dictionary: Dictionary, board: Board):
        self.dictionary = dictionary
        self.board = board
        self.rack = []

    def set_rack(self, rack):
        self.rack = [letter.lower() for letter in rack]

    def get_possible_words(self):
        valid_words = set()

        for length in range(len(self.rack), 0, -1):
            if self.board.board_is_empty():
                for word in self.find_words_for_series(["-" for _ in range(length)]):
                    valid_words.add(
                        (
                            word,
                            (
                                self.board.board_dimension // 2,
                                self.board.board_dimension // 2,
                            ),
                            Direction.HORIZONTAL,
                        )
                    )
            else:
                for row in range(self.board.board_dimension):
                    for col in range(self.board.board_dimension):
                        if col + length <= self.board.board_dimension:
                            if col > 0 and self.board.get_cell(row, col - 1) != "-":
                                continue
                            r = self.board.get_series(
                                row, col, length, Direction.HORIZONTAL
                            )
                            if len(r) > length:
                                for word in self.find_words_for_series(r):
                                    valid_words.add(
                                        (word, (row, col), Direction.HORIZONTAL)
                                    )

                        if row + length <= self.board.board_dimension:
                            if row > 0 and self.board.get_cell(row - 1, col) != "-":
                                continue
                            r = self.board.get_series(
                                row, col, length, Direction.VERTICAL
                            )
                            if len(r) > length:
                                for word in self.find_words_for_series(r):
                                    valid_words.add(
                                        (word, (row, col), Direction.VERTICAL)
                                    )

        return valid_words

    def get_scored_possible_words(self):
        possible_words = self.get_possible_words()
        scored_words = []

        for word, (row, col), direction in possible_words:
            board_copy = copy.deepcopy(self.board)

            try:
                existing_words = set(
                    word_tuple[0] for word_tuple in board_copy.get_words()
                )

                board_copy.add_word(word, row, col, direction)

                all_words_after = set(
                    word_tuple for word_tuple in board_copy.get_words()
                )

                new_words = [
                    word_tuple
                    for word_tuple in all_words_after
                    if word_tuple[0] not in existing_words
                ]

                if self.is_board_valid(board_copy):
                    total_score = sum(
                        self.board.get_word_score(self.rack, w, r, c, direction)
                        for w, (r, c), d in new_words
                    )

                    scored_words.append((word, (row, col), direction, total_score))

            except ValueError:
                continue

        return sorted(scored_words, key=lambda x: x[3], reverse=True)

    def find_words_for_series(self, series=[]):
        valid_words = set()

        for word in self.dictionary.search_with_pattern("".join(series)):
            rack_copy = copy.copy(self.rack)
            for i, letter in enumerate(word):
                if letter not in rack_copy and series[i] != letter:
                    if "?" in rack_copy:
                        rack_copy.remove("?")
                        continue
                    break
                if series[i] != letter:
                    rack_copy.remove(letter)
                if i == len(word) - 1:
                    valid_words.add(word)

        return valid_words

    def is_board_valid(self, board=None):
        if board is None:
            board = self.board

        words = board.get_words()
        for word in words:
            if not self.dictionary.search(word[0]):
                return False

        return True
