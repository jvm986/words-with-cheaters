import json

from tile import Tile


class RackEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Tile):
            return obj.__dict__
        return super().default(obj)


class Rack:
    def __init__(self, tiles: list[Tile]):
        self.tiles = tiles

    def __repr__(self):
        return " ".join([str(tile.letter) for tile in self.tiles])

    def __str__(self):
        return self.__repr__()

    @classmethod
    def from_parsed_rack(cls, parsed_rack: list[tuple[str, int]]) -> "Rack":
        return cls([Tile(letter, score) for letter, score in parsed_rack])

    @classmethod
    def load_rack_from_file(cls, file_path: str) -> "Rack":
        with open(file_path, "r") as file:
            rack_data = json.load(file)

        return cls([Tile(tile["letter"], tile["score"]) for tile in rack_data])

    def save_rack_to_file(self, file_path: str):
        with open(file_path, "w") as file:
            json.dump(
                [tile.__dict__ for tile in self.tiles],
                file,
                indent=2,
                cls=RackEncoder,
            )

    def get_letters(self):
        return [tile.letter for tile in self.tiles]

    def get_scores(self):
        return [tile.score for tile in self.tiles]

    def print_letters(self):
        print(" ".join(self.get_letters()))

    def print_scores(self):
        print(" ".join(str(score) for score in self.get_scores()))
