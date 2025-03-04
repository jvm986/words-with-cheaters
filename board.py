import copy
import csv
from enum import Enum
from typing import List


class Direction(Enum):
    HORIZONTAL = 1
    VERTICAL = 2


class Board:
    def __init__(
        self,
        board_dimension: int,
        board_file=None,
        multipliers_file=None,
        letter_scores_file=None,
    ):
        self.board_dimension = board_dimension
        self.board = [
            ["-" for _ in range(board_dimension)] for _ in range(board_dimension)
        ]
        self.multipliers = [
            ["-" for _ in range(board_dimension)] for _ in range(board_dimension)
        ]
        self.letter_scores = (
            self.load_letter_scores_from_file(letter_scores_file)
            if letter_scores_file
            else self.default_letter_scores()
        )

        if board_file:
            self.load_board_from_file(board_file)

        if multipliers_file:
            self.load_multipliers_from_file(multipliers_file)

    def default_letter_scores(self):
        return {
            "a": 1,
            "b": 4,
            "c": 4,
            "d": 2,
            "e": 1,
            "f": 4,
            "g": 3,
            "h": 4,
            "i": 1,
            "j": 8,
            "k": 5,
            "l": 1,
            "m": 3,
            "n": 1,
            "o": 1,
            "p": 4,
            "q": 10,
            "r": 1,
            "s": 1,
            "t": 1,
            "u": 2,
            "v": 4,
            "w": 4,
            "x": 8,
            "y": 4,
            "z": 10,
        }

    def load_letter_scores_from_file(self, file_path: str):
        scores = {}
        with open(file_path, newline="") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) == 2:
                    letter, score = row[0].lower(), int(row[1])
                    scores[letter] = score
        return scores

    def load_board_from_file(self, board_file: str):
        with open(board_file, newline="") as csvfile:
            reader = csv.reader(csvfile)
            for i, row in enumerate(reader):
                self.board[i] = [str(cell).lower() for cell in row]

    def save_board_to_file(self, board_file: str):
        with open(board_file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            for row in self.board:
                writer.writerow(row)

    def load_multipliers_from_file(self, multipliers_file: str):
        with open(multipliers_file, newline="") as csvfile:
            reader = csv.reader(csvfile)
            for i, row in enumerate(reader):
                for j, cell in enumerate(row):
                    self.multipliers[i][j] = cell

    def print_board(self):
        for row in self.board:
            print(" ".join(row))

    def get_cell(self, row: int, col: int):
        return self.board[row][col]

    def get_words(self):
        words_with_indexes = []

        # Extract horizontal words
        for row_idx, row in enumerate(self.board):
            row_string = "".join(row)
            row_words = row_string.split("-")
            start_col = 0

            for word in row_words:
                if len(word) > 1:
                    words_with_indexes.append(
                        (word, (row_idx, start_col), Direction.HORIZONTAL)
                    )
                start_col += len(word) + 1  # Move past the word and the delimiter

        # Extract vertical words
        for col_idx in range(self.board_dimension):
            col_string = "".join(
                self.board[row][col_idx] for row in range(self.board_dimension)
            )
            col_words = col_string.split("-")
            start_row = 0

            for word in col_words:
                if len(word) > 1:
                    words_with_indexes.append(
                        (word, (start_row, col_idx), Direction.VERTICAL)
                    )
                start_row += len(word) + 1  # Move past the word and the delimiter

        return words_with_indexes

    def get_range(self, row: int, col: int, to_place: int, direction: Direction):
        result = []
        count = 0

        if direction == Direction.HORIZONTAL:
            for i in range(self.board_dimension):
                if i + col < self.board_dimension:
                    cell = self.board[row][col + i]
                    if cell == "-" and count >= to_place:
                        break
                    result.append(cell)
                    if cell == "-":
                        count += 1

        elif direction == Direction.VERTICAL:
            for i in range(self.board_dimension):
                if i + row < self.board_dimension:
                    cell = self.board[row + i][col]
                    if cell == "-" and count >= to_place:
                        break
                    result.append(cell)
                    if cell == "-":
                        count += 1

        else:
            raise ValueError("Invalid direction")

        if count < to_place:
            return []

        return result

    def board_is_empty(self):
        for row in self.board:
            for cell in row:
                if cell != "-":
                    return False
        return True

    def word_intersects_center(
        self, word: str, row: int, col: int, direction: Direction
    ):
        if direction == Direction.HORIZONTAL:
            return (
                row == self.board_dimension // 2
                and col <= self.board_dimension // 2 < col + len(word)
            )
        elif direction == Direction.VERTICAL:
            return (
                col == self.board_dimension // 2
                and row <= self.board_dimension // 2 < row + len(word)
            )
        else:
            raise ValueError("Invalid direction")

    def word_is_placable(self, word: str, row: int, col: int, direction: Direction):
        board_is_empty = self.board_is_empty()
        intersects_center = self.word_intersects_center(word, row, col, direction)

        if direction == Direction.HORIZONTAL:
            if col + len(word) > self.board_dimension:
                return False

            intersects = False
            for i, letter in enumerate(word):
                board_cell = self.board[row][col + i]

                if board_cell != "-" and board_cell != letter:
                    return False  # Conflict with an existing tile

                if board_cell == letter:
                    intersects = True  # Ensure at least one letter aligns

            return intersects or (board_is_empty and intersects_center)

        elif direction == Direction.VERTICAL:
            if row + len(word) > self.board_dimension:
                return False

            intersects = False
            for i, letter in enumerate(word):
                board_cell = self.board[row + i][col]

                if board_cell != "-" and board_cell != letter:
                    return False  # Conflict with an existing tile

                if board_cell == letter:
                    intersects = True  # Ensure at least one letter aligns

            return intersects or (board_is_empty and intersects_center)

        else:
            raise ValueError("Invalid direction")

    def add_word(self, word: str, row: int, col: int, direction: Direction):
        if not self.word_is_placable(word, row, col, direction):
            raise ValueError("Word is not placable")

        if direction == Direction.HORIZONTAL:
            for i, letter in enumerate(word):
                self.board[row][col + i] = letter.lower()
        elif direction == Direction.VERTICAL:
            for i, letter in enumerate(word):
                self.board[row + i][col] = letter.lower()
        else:
            raise ValueError("Invalid direction")

    def letter_score(self, letter: str):
        return self.letter_scores[letter]

    def letter_multiplier(self, row: int, col: int):
        multiplier = self.multipliers[row][col]
        if multiplier.isdigit():
            return int(multiplier)
        return 1

    def word_multiplier(self, row: int, col: int):
        multiplier = self.multipliers[row][col]
        if multiplier == "T":
            return 3
        elif multiplier == "D":
            return 2
        return 1

    def get_word_score(
        self, rack: List[str], word: str, row: int, col: int, direction: Direction
    ):
        if not self.word_is_placable(word, row, col, direction):
            raise ValueError("Word is not placable")

        score = 0
        word_multiplier = 1
        rack_copy = copy.copy(rack)

        if direction == Direction.HORIZONTAL:
            for i, letter in enumerate(word):
                cell = self.get_cell(row, col + i)
                letter_score = self.letter_scores[letter]
                letter_multiplier = self.letter_multiplier(row, col + i)

                if cell == "-":
                    if not letter in rack_copy:
                        if not "?" in rack_copy:
                            raise ValueError("Invalid placement")
                        rack_copy.remove("?")
                        continue
                    score += letter_score * letter_multiplier
                    word_multiplier *= self.word_multiplier(row, col + i)
                    rack_copy.remove(letter)
                elif cell == letter:
                    score += letter_score
                else:
                    raise ValueError("Invalid placement")

        elif direction == Direction.VERTICAL:
            for i, letter in enumerate(word):
                cell = self.get_cell(row + i, col)
                letter_score = self.letter_scores[letter]
                letter_multiplier = self.letter_multiplier(row + i, col)

                if cell == "-":
                    if not letter in rack_copy:
                        if not "?" in rack_copy:
                            raise ValueError("Invalid placement")
                        rack_copy.remove("?")
                        continue
                    score += letter_score * letter_multiplier
                    word_multiplier *= self.word_multiplier(row + i, col)
                    rack_copy.remove(letter)
                elif cell == letter:
                    score += letter_score
                else:
                    raise ValueError("Invalid placement")

        else:
            raise ValueError("Invalid direction")

        score = score * word_multiplier

        if len(rack_copy) == 0:
            score += 40

        return score
