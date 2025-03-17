from typing import Dict, List, Optional, Set, Tuple

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
        valid_words: List[Word] = []
        unusable_series: Set[str] = set()

        for series_length in range(len(self.rack.tiles), 0, -1):
            if self.board.is_board_empty():
                for word in self.find_words_for_series(
                    self.board.get_empty_board_series(series_length), unusable_series
                ):
                    valid_words.append(word)
            else:
                for row in range(self.board.rows):
                    for col in range(self.board.cols):
                        if col + series_length <= self.board.cols:
                            if col > 0 and str(self.board.get_cell(row, col - 1)) != "-":
                                continue
                            series = self.board.get_series(row, col, series_length, Direction.HORIZONTAL)
                            for word in self.find_words_for_series(series, unusable_series):
                                valid_words.append(word)

                        if row + series_length <= self.board.rows:
                            if row > 0 and str(self.board.get_cell(row - 1, col)) != "-":
                                continue
                            series = self.board.get_series(row, col, series_length, Direction.VERTICAL)
                            for word in self.find_words_for_series(series, unusable_series):
                                valid_words.append(word)

        return valid_words

    def count_placed_tiles(self, words: List[Word]) -> int:
        unique_cells: List[Cell] = []
        for word in words:
            for cell in word.cells:
                if cell not in unique_cells:
                    unique_cells.append(cell)

        placed_tiles_count = 0
        for cell in unique_cells:
            if not self.board.get_cell(cell.row, cell.col).tile:
                placed_tiles_count += 1

        return placed_tiles_count

    def get_scored_possible_words(self) -> List[Tuple[List[Word], int, int]]:
        possible_words = self.get_possible_words()
        scored_words: List[Tuple[List[Word], int, int]] = []

        existing_words = self.board.get_board_words()
        for word in possible_words:
            board_copy = self.board.clone()

            try:
                board_copy.add_word(word)
            except ValueError:
                continue

            all_words_after = board_copy.get_board_words()
            new_words = [word for word in all_words_after if word not in existing_words]

            total_score = 0

            for new_word in new_words:
                total_score += new_word.get_score()
                if self.count_placed_tiles([new_word]) == 7:
                    total_score += 40

            try:
                self.validate_board(board_copy)
            except ValueError:
                continue

            scored_words.append((new_words, total_score, self.count_placed_tiles(new_words)))

        return sorted(scored_words, key=lambda x: x[1], reverse=True)

    def find_words_for_series(self, series: List[Cell], unusable_series: Set[str]) -> List[Word]:
        valid_words: List[Word] = []
        series_str = "".join(str(cell) for cell in series)

        for word in self.dictionary.search_with_pattern(series_str):
            rack_dict = {tile.letter: tile.score for tile in self.rack.tiles}
            cells: List[Cell] = []

            if series_str + word in unusable_series:
                continue

            for i, letter in enumerate(word):
                series_letter_string = series[i].get_letter_string()
                if letter not in rack_dict and series_letter_string != letter:
                    if "?" in rack_dict:
                        score = rack_dict.pop("?")
                        cells.append(
                            Cell(
                                series[i].row,
                                series[i].col,
                                Tile(letter, score),
                                series[i].multiplier,
                            )
                        )
                        continue
                    unusable_series.add(series_str + word)
                    break
                if series_letter_string != letter:
                    score = rack_dict.pop(letter)
                    cells.append(
                        Cell(
                            series[i].row,
                            series[i].col,
                            Tile(letter, score),
                            series[i].multiplier,
                        )
                    )
                else:
                    cells.append(series[i])
                if i == len(word) - 1:
                    valid_words.append(Word(cells))

        return valid_words

    def validate_board(self, board: Optional[Board] = None) -> None:
        if board is None:
            board = self.board

        words = board.get_board_words()
        for word in words:
            if not self.dictionary.search(str(word)):
                raise ValueError(f"Word {word} is not in the dictionary")
