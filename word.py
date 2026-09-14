from typing import Any, List, Optional, Set, Tuple

from cell import Cell


class Word:
    def __init__(self, cells: List[Cell]):
        for cell in cells:
            if cell.tile is None:
                raise ValueError("Word must contain only tiles")

        self.cells = cells

    def __repr__(self) -> str:
        return "".join([str(cell.tile) for cell in self.cells])

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, value: Any) -> bool:
        if not isinstance(value, Word):
            return False
        return self.cells == value.cells

    def get_score(self, placed_positions: Optional[Set[Tuple[int, int]]] = None) -> int:
        score = 0
        word_multiplier = 1
        for cell in self.cells:
            multiplier = (
                cell.multiplier if placed_positions is None or (cell.row, cell.col) in placed_positions else None
            )
            letter_multiplier = multiplier.letter_multiplier() if multiplier else 1
            letter_score = cell.tile.score * letter_multiplier if cell.tile else 0
            score += letter_score
            word_multiplier *= multiplier.word_multiplier() if multiplier else 1

        return score * word_multiplier
