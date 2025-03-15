import unittest
import json
import os
from rack import Rack, RackEncoder
from tile import Tile


class TestRack(unittest.TestCase):
    def setUp(self):
        """Set up common test variables."""
        self.tile_A = Tile(letter="A", score=1)
        self.tile_B = Tile(letter="B", score=3)
        self.tile_C = Tile(letter="C", score=3)

        self.rack = Rack([self.tile_A, self.tile_B, self.tile_C])

    def test_rack_creation(self):
        """Test that a Rack is correctly created with valid tiles."""
        self.assertEqual(str(self.rack), "A B C")
        self.assertEqual(self.rack.get_letters(), ["A", "B", "C"])

    def test_rack_from_parsed_rack(self):
        """Test creating a Rack from parsed data."""
        parsed_rack = [("X", 8), ("Y", 4)]
        rack = Rack.from_parsed_rack(parsed_rack)
        self.assertEqual(str(rack), "X Y")
        self.assertEqual(rack.get_letters(), ["X", "Y"])

    def test_rack_pop_tile(self):
        """Test removing a tile from the rack."""
        tile = self.rack.pop_tile("B")
        self.assertEqual(tile.letter, "B")
        self.assertEqual(self.rack.get_letters(), ["A", "C"])

    def test_rack_pop_tile_not_found(self):
        """Test attempting to remove a tile that doesn't exist."""
        tile = self.rack.pop_tile("Z")
        self.assertIsNone(tile)
        self.assertEqual(self.rack.get_letters(), ["A", "B", "C"])

    def test_rack_save_and_load_from_file(self):
        """Test saving and loading a rack from a file."""
        file_path = "test_rack.json"

        self.rack.save_rack_to_file(file_path)

        loaded_rack = Rack.load_rack_from_file(file_path)

        self.assertEqual(str(loaded_rack), "A B C")
        self.assertEqual(loaded_rack.get_letters(), ["A", "B", "C"])

        os.remove(file_path)

    def test_rack_encoder(self):
        """Test JSON encoding of a rack."""
        encoded_rack = json.dumps(self.rack.tiles, cls=RackEncoder)
        decoded_rack = json.loads(encoded_rack)

        self.assertEqual(
            decoded_rack,
            [
                {"letter": "A", "score": 1},
                {"letter": "B", "score": 3},
                {"letter": "C", "score": 3},
            ],
        )


if __name__ == "__main__":
    unittest.main()
