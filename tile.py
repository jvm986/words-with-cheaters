class Tile:
    def __init__(self, letter: str, score: int):
        if letter and len(letter) > 1:
            raise ValueError("Letter must be a single character")
        self.letter = letter
        self.score = score

    def __repr__(self):
        return self.letter

    def __eq__(self, value):
        return self.letter == value.letter and self.score == value.score

    def to_json(self):
        return {
            "letter": self.letter,
            "score": self.score,
        }

    @classmethod
    def from_json(cls, data):
        return cls(data["letter"], data["score"])
