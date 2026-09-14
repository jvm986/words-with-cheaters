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

        empty_board = self.board.is_board_empty()
        for series_length in range(len(self.rack.tiles), 0, -1):
            for row in range(self.board.rows):
                for col in range(self.board.cols):
                    for direction in Direction:
                        dr, dc = (0, 1) if direction == Direction.HORIZONTAL else (1, 0)
                        if row - dr >= 0 and col - dc >= 0:
                            if self.board.get_cell(row - dr, col - dc).tile is not None:
                                continue
                        series = self.board.get_series(row, col, series_length, direction)
                        if not series:
                            continue
                        if empty_board:
                            if not any(
                                cell.row == self.board.rows // 2 and cell.col == self.board.cols // 2 for cell in series
                            ):
                                continue
                        elif not self.board.cell_in_series_touches_tile(series):
                            continue
                        valid_words.extend(self.find_words_for_series(series, unusable_series))

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

            placed_positions = {
                (cell.row, cell.col) for cell in word.cells if self.board.get_cell(cell.row, cell.col).tile is None
            }
            if not new_words or not placed_positions:
                continue
            total_score = sum(new_word.get_score(placed_positions) for new_word in new_words)
            if len(placed_positions) == 7:
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
            cache_key = series_str + word
            if cache_key in unusable_series:
                continue
            rack_counts: Dict[Tuple[str, int], int] = {}
            for tile in self.rack.tiles:
                key = (tile.letter, tile.score)
                rack_counts[key] = rack_counts.get(key, 0) + 1
            cells: List[Cell] = []
            before = len(valid_words)

            def place(index: int) -> None:
                if index == len(word):
                    valid_words.append(Word(list(cells)))
                    return
                cell = series[index]
                letter = word[index]
                if cell.tile is not None:
                    cells.append(cell)
                    place(index + 1)
                    cells.pop()
                    return
                # Explore natural tiles and blanks: their positions affect premiums and crosswords.
                for key, count in rack_counts.items():
                    rack_letter, score = key
                    if count == 0 or rack_letter not in (letter, "?"):
                        continue
                    rack_counts[key] -= 1
                    cells.append(
                        Cell(cell.row, cell.col, Tile(letter, 0 if rack_letter == "?" else score), cell.multiplier)
                    )
                    place(index + 1)
                    cells.pop()
                    rack_counts[key] += 1

            place(0)
            if len(valid_words) == before:
                unusable_series.add(cache_key)

        return valid_words

    def validate_board(self, board: Optional[Board] = None) -> None:
        if board is None:
            board = self.board

        words = board.get_board_words()
        for word in words:
            if not self.dictionary.search(str(word)):
                raise ValueError(f"Word {word} is not in the dictionary")
