from typing import Any, Dict


class Tile:
    def __init__(self, letter: str, score: int):
        if letter and len(letter) > 1:
            raise ValueError("Letter must be a single character")
        self.letter = letter
        self.score = score

    def __repr__(self) -> str:
        return self.letter

    def __eq__(self, value: Any) -> bool:
        if not isinstance(value, Tile):
            return False
        return self.letter == value.letter and self.score == value.score

    def to_json(self) -> Dict[str, Any]:
        return {
            "letter": self.letter,
            "score": self.score,
        }

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "Tile":
        return cls(data["letter"], data["score"])
