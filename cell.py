from enum import Enum
import logging
from typing import Any, Optional

from tile import Tile


class Multiplier(Enum):
    DL = 1
    TL = 2
    DW = 3
    TW = 4

    def to_json(self) -> str:
        return self.name

    @classmethod
    def from_json(cls, name: str) -> "Multiplier":
        return cls[name]

    def letter_multiplier(self) -> int:
        if self == Multiplier.DL:
            return 2
        if self == Multiplier.TL:
            return 3
        return 1

    def word_multiplier(self) -> int:
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

    def __repr__(self) -> str:
        if self.tile:
            return str(self.tile)
        return "-"

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, value: Any) -> bool:
        if not isinstance(value, Cell):
            return False
        return (
            self.row == value.row
            and self.col == value.col
            and self.tile == value.tile
            and self.multiplier == value.multiplier
        )

    @classmethod
    def from_parsed_cell(cls, letter: str, score: int, row: int, col: int) -> "Cell":
        if letter in ["", " ", "_", "Ø", None]:
            if score != 0:
                logging.warning(f"Empty tile has a score: {score}, row: {row}, col: {col}")
            return Cell(row, col)
        if letter in ["DL", "TL", "DW", "TW"]:
            return Cell(row, col, multiplier=Multiplier[letter])
        return Cell(row, col, tile=Tile(letter[0], score))

    def get_letter_string(self) -> str:
        if self.tile:
            return self.tile.letter
        return "-"

    def to_json(self) -> dict[str, Any]:
        return {
            "row": self.row,
            "col": self.col,
            "tile": self.tile.to_json() if self.tile else None,
            "multiplier": self.multiplier.name if self.multiplier else None,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Cell":
        return cls(
            row=data["row"],
            col=data["col"],
            tile=Tile.from_json(data["tile"]) if data["tile"] else None,
            multiplier=Multiplier[data["multiplier"]] if data["multiplier"] else None,
        )
