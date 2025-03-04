# Words with Cheaters

### Usage

Copy Board

```bash
cp empty_board.csv board.csv
```

Run solver with board file and rack as arguments. There are no dependencies other than the Python standard library, so a virtual environment is not strictly necessary.

```bash
python3 main.py board.csv 'abcd?fg'
```

The algorithm could be a lot faster but it generally solves for all possible words in <2 seconds for a 15x15 board with 7 tiles, including wild cards on an M2.

The way it works is to check every valid range on the board (a valid range includes an intersection with another tile) for every length of word at and below the rack length as a pattern in the dictionary. It then checks if the rack can satisfy the resulting words before checking the whole board for validty and scoring the placement.

### TODO

- Previously used wild cards should not count for points in any future moves. This will need to be encoded in the board state.
- Parse a screenshot of the board and rack to get the board state and rack.
- Serve the solver as an API, running this on a smaller machine might show that a optimized algorithm is necessary.
- The dictionary does not align perfectly with wordfeud.
