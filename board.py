import json
from enum import Enum
from typing import Any, List, Optional

from cell import Cell, Multiplier
from tile import Tile
from word import Word


class Direction(Enum):
    HORIZONTAL = 1
    VERTICAL = 2

    def to_json(self) -> str:
        return self.name

    @classmethod
    def from_json(cls, name: str) -> "Direction":
        return cls[name]


class BoardEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Enum):
            return o.name
        if isinstance(o, Tile):
            return o.to_json()
        if isinstance(o, Cell):
            return o.to_json()
        return super().default(o)


class Board:
    def __init__(
        self,
        cells: list[list[Cell]],
    ):
        self.cells = cells
        self.rows = len(cells)
        self.cols = len(cells[0])
        self.validate_board()

    @classmethod
    def load_board_from_file(cls, file_path: str) -> "Board":
        """Loads a board from a JSON file using a custom decoder."""
        with open(file_path, "r") as file:
            board_data = json.load(file)

        board = [
            [
                Cell(
                    row=cell.get("row"),
                    col=cell.get("col"),
                    tile=(
                        Tile(cell["tile"]["letter"], cell["tile"]["score"]) if cell.get("tile") is not None else None
                    ),
                    multiplier=(Multiplier[cell["multiplier"]] if cell.get("multiplier") is not None else None),
                )
                for cell in row
            ]
            for row in board_data
        ]

        return cls(board)

    def save_board_to_file(self, file_path: str) -> None:
        """Saves the board to a JSON file using a custom encoder."""
        with open(file_path, "w") as file:
            json.dump(self.cells, file, indent=2, cls=BoardEncoder)

    def validate_board(self) -> None:
        if not self.cells:
            raise ValueError("Board is empty")

        for r, row in enumerate(self.cells):
            if len(row) != self.cols:
                raise ValueError(f"Row {r} has incorrect length")

    def get_cell(self, row: int, col: int) -> Cell:
        return self.cells[row][col]

    def is_cell_middle(self, row: int, col: int) -> bool:
        cell = self.get_cell(row, col)
        return cell.row == self.rows // 2 and cell.col == self.cols // 2 and cell.tile is None

    def get_words_from_series(self, series: List[Cell]) -> List[Word]:
        words: List[Word] = []
        current_word: Optional[List[Cell]] = None

        for cell in series:
            if cell.tile:
                if current_word is None:
                    current_word = []
                current_word.append(cell)
            elif current_word:
                if len(current_word) > 1:
                    words.append(Word(current_word))
                current_word = None

        if current_word and len(current_word) > 1:
            words.append(Word(current_word))

        return words

    def get_row(self, row: int) -> List[Cell]:
        return self.cells[row]

    def get_col(self, col: int) -> List[Cell]:
        return [row[col] for row in self.cells]

    def get_board_words(self) -> List[Word]:
        self.validate_board()

        words: List[Word] = []

        for row_idx in range(len(self.cells)):
            row = self.get_row(row_idx)
            row_words = self.get_words_from_series(row)
            words.extend(row_words)

        for col_idx in range(len(self.cells[0])):
            col = self.get_col(col_idx)
            col_words = self.get_words_from_series(col)
            words.extend(col_words)

        return words

    def get_series(self, row: int, col: int, to_place: int, direction: Direction) -> List[Cell]:
        series: List[Cell] = []
        count = 0

        if direction == Direction.HORIZONTAL:
            for i in range(self.rows):
                if i + col < self.cols:
                    cell = self.cells[row][col + i]
                    if cell.tile is None and count >= to_place:
                        break
                    series.append(cell)
                    if cell.tile is None:
                        count += 1

        elif direction == Direction.VERTICAL:
            for i in range(self.rows):
                if i + row < self.cols:
                    cell = self.cells[row + i][col]
                    if cell.tile is None and count >= to_place:
                        break
                    series.append(cell)
                    if cell.tile is None:
                        count += 1

        else:
            raise ValueError("Invalid direction")

        if count < to_place:
            return []

        return series

    def get_empty_board_series(self, to_place: int) -> List[Cell]:
        series: List[Cell] = []
        middle = self.rows // 2, self.cols // 2

        for i in range(to_place):
            series.append(self.cells[middle[0]][middle[1] + i])

        return series

    def is_board_empty(self) -> bool:
        for row in self.cells:
            for cell in row:
                if cell.tile is not None:
                    return False
        return True

    def word_intersects_center(self, word: Word) -> bool:
        for cell in word.cells:
            if cell.row == self.rows // 2 and cell.col == self.cols // 2:
                return True
        return False

    def word_is_placable(self, word: Word) -> bool:
        for cell in word.cells:
            board_cell = self.get_cell(cell.row, cell.col)
            if board_cell.tile is not None:
                if not board_cell.tile or not cell.tile or board_cell.tile.letter != cell.tile.letter:
                    raise ValueError(f"Invalid cell placement {cell}")

        return self.cell_in_series_touches_tile(word.cells) or (
            self.is_board_empty() and self.word_intersects_center(word)
        )

    def add_word(self, word: Word) -> None:
        if not self.word_is_placable(word):
            raise ValueError("Word is not placable")

        for cell in word.cells:
            board_cell = self.get_cell(cell.row, cell.col)
            if board_cell.tile is None:
                self.cells[cell.row][cell.col] = cell

    def clone(self) -> "Board":
        new_board = Board([[cell for cell in row] for row in self.cells])
        return new_board

    def cell_touches_tile(self, row: int, col: int) -> bool:
        if self.get_cell(row, col).tile is not None:
            return True

        if row > 0 and self.get_cell(row - 1, col).tile is not None:
            return True

        if row < self.rows - 1 and self.get_cell(row + 1, col).tile is not None:
            return True

        if col > 0 and self.get_cell(row, col - 1).tile is not None:
            return True

        if col < self.cols - 1 and self.get_cell(row, col + 1).tile is not None:
            return True

        return False

    def cell_in_series_touches_tile(self, series: List[Cell]) -> bool:
        for cell in series:
            if self.cell_touches_tile(cell.row, cell.col):
                return True
        return False

    def print_letters(self) -> None:
        for row in self.cells:
            for cell in row:
                if cell.tile:
                    print(f"{cell.tile.letter:<2}", end=" ")
                else:
                    print("- ", end=" ")
            print()
        print()

    def print_scores(self) -> None:
        for row in self.cells:
            for cell in row:
                if cell.tile:
                    print(f"{cell.tile.score:<2}", end=" ")
                else:
                    print("- ", end=" ")
            print()
        print()

    def print_mutlipliers(self) -> None:
        for row in self.cells:
            for cell in row:
                if cell.multiplier:
                    print(f"{cell.multiplier.name:<2}", end=" ")
                else:
                    print("- ", end=" ")
            print()
        print()
