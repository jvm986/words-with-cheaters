import json
from typing import Any, List

from tile import Tile


class RackEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Tile):
            return o.to_json()
        return super().default(o)


class Rack:
    def __init__(self, tiles: list[Tile]):
        self.tiles = tiles

    def __repr__(self) -> str:
        return " ".join([str(tile.letter) for tile in self.tiles])

    def __str__(self) -> str:
        return self.__repr__()

    @classmethod
    def from_parsed_rack(cls, parsed_rack: list[tuple[str, int]]) -> "Rack":
        return cls([Tile(letter, score) for letter, score in parsed_rack])

    @classmethod
    def load_rack_from_file(cls, file_path: str) -> "Rack":
        with open(file_path, "r") as file:
            rack_data = json.load(file)

        return cls([Tile(tile["letter"], tile["score"]) for tile in rack_data])

    def save_rack_to_file(self, file_path: str) -> None:
        with open(file_path, "w") as file:
            json.dump(
                [tile.__dict__ for tile in self.tiles],
                file,
                indent=2,
                cls=RackEncoder,
            )

    def get_letters(self) -> List[str]:
        return [tile.letter for tile in self.tiles]

    def get_scores(self) -> List[int]:
        return [tile.score for tile in self.tiles]

    def print_letters(self) -> None:
        print(" ".join(self.get_letters()))

    def print_scores(self) -> None:
        print(" ".join(str(score) for score in self.get_scores()))
