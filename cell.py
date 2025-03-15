from enum import Enum
from typing import Optional

from tile import Tile


class Multiplier(Enum):
    DL = 1
    TL = 2
    DW = 3
    TW = 4

    def __eq__(self, value):
        return super().__eq__(value)

    def to_json(self):
        return self.name

    @classmethod
    def from_json(cls, name: str):
        return cls[name]

    def letter_multiplier(self):
        if self == Multiplier.DL:
            return 2
        if self == Multiplier.TL:
            return 3
        return 1

    def word_multiplier(self):
        if self == Multiplier.DW:
            return 2
        if self == Multiplier.TW:
            return 3
        return 1


class Cell:
    def __init__(
        self,
        row: int,
        col: int,
        tile: Optional[Tile] = None,
        multiplier: Optional[Multiplier] = None,
    ):
        self.row = row
        self.col = col
        self.tile = tile
        self.multiplier = multiplier

        if row is None or col is None:
            raise ValueError("Cell must have a row and column")

    def __repr__(self):
        if self.tile:
            return str(self.tile)
        return "-"

    def __str__(self):
        return self.__repr__()

    def __eq__(self, value):
        return (
            self.row == value.row
            and self.col == value.col
            and self.tile == value.tile
            and self.multiplier == value.multiplier
        )

    @classmethod
    def from_parsed_cell(cls, letter: str, score: int, row: int, col: int) -> "Cell":
        if letter in ["" " ", "_", "EMPTY", "MIDDLE", None]:
            return Cell(row, col)
        if letter in ["DL", "TL", "DW", "TW"]:
            return Cell(row, col, multiplier=Multiplier[letter])
        return Cell(row, col, tile=Tile(letter, score))

    def get_letter_string(self):
        if self.tile:
            return self.tile.letter
        return "-"
