from typing import List, Tuple

from board import Board, Direction
from cell import Cell
from dictionary import Dictionary
from rack import Rack
from tile import Tile
from word import Word


class Game:
    def __init__(self, dictionary: Dictionary, board: Board, rack: Rack):
        self.dictionary = dictionary
        self.board = board
        self.rack = rack

    def get_possible_words(self) -> List[Word]:
        valid_words = []

        for series_length in range(len(self.rack.tiles), 0, -1):
            if self.board.board_is_empty():
                for word in self.find_words_for_series(self.board.get_empty_board_series(series_length)):
                    valid_words.append(word)
            else:
                for row in range(self.board.rows):
                    for col in range(self.board.cols):
                        if col + series_length <= self.board.cols:
                            if col > 0 and str(self.board.get_cell(row, col - 1)) != "-":
                                continue
                            series = self.board.get_series(row, col, series_length, Direction.HORIZONTAL)
                            for word in self.find_words_for_series(series):
                                valid_words.append(word)

                        if row + series_length <= self.board.rows:
                            if row > 0 and str(self.board.get_cell(row - 1, col)) != "-":
                                continue
                            series = self.board.get_series(row, col, series_length, Direction.VERTICAL)
                            for word in self.find_words_for_series(series):
                                valid_words.append(word)

        return valid_words

    def is_word_bingo(self, word: Word) -> bool:
        existing_tiles_count = 0
        for cell in word.cells:
            if self.board.get_cell(cell.row, cell.col).tile:
                existing_tiles_count += 1

        placed_tiles_count = len(word.cells) - existing_tiles_count

        return placed_tiles_count == 7

    def get_scored_possible_words(self) -> List[Tuple[List[Word], int]]:
        possible_words = self.get_possible_words()
        scored_words = []

        for word in possible_words:
            board_copy = self.board.clone()

            existing_words = board_copy.get_board_words()

            try:
                board_copy.add_word(word)
            except ValueError:
                continue

            all_words_after = board_copy.get_board_words()
            new_words = [word for word in all_words_after if word not in existing_words]

            total_score = 0

            for new_word in new_words:
                total_score += new_word.get_score()
                if self.is_word_bingo(new_word):
                    total_score += 40

            try:
                self.validate_board(board_copy)
            except ValueError:
                continue

            scored_words.append((new_words, total_score))

        return sorted(scored_words, key=lambda x: x[1], reverse=True)

    def find_words_for_series(self, series: List[Cell]) -> List[Word]:
        valid_words = []

        for word in self.dictionary.search_with_pattern("".join(str(cell) for cell in series)):
            rack_copy = Rack(self.rack.tiles.copy())
            cells = []
            for i, letter in enumerate(word):
                if letter not in rack_copy.get_letters() and series[i].get_letter_string() != letter:
                    if "?" in rack_copy.get_letters():
                        rack_tile = rack_copy.pop_tile("?")
                        cells.append(
                            Cell(
                                series[i].row,
                                series[i].col,
                                Tile(letter, rack_tile.score),
                                series[i].multiplier,
                            )
                        )
                        continue
                    break
                if series[i].get_letter_string() != letter:
                    rack_tile = rack_copy.pop_tile(letter)
                    cells.append(
                        Cell(
                            series[i].row,
                            series[i].col,
                            Tile(letter, rack_tile.score),
                            series[i].multiplier,
                        )
                    )
                else:
                    cells.append(series[i])
                if i == len(word) - 1:
                    valid_words.append(Word(cells))

        return valid_words

    def validate_board(self, board=None) -> None:
        if board is None:
            board = self.board

        words = board.get_board_words()
        for word in words:
            if not self.dictionary.search(str(word)):
                raise ValueError(f"Word {word} is not in the dictionary")
