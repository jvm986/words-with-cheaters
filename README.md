# Words with Cheaters

A wordfeud solver that uses a fine-tuned tesseract model to parse the board and rack from a screenshot and then solves for the highest scoring move.

### Requirements

- Python 3.12
- Tessaract OCR (`brew install tesseract`)

### Installation

Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Set the `TESSDATA_PREFIX` environment variable to the dataset directory:

```bash
export TESSDATA_PREFIX=$(pwd)/dataset
```

### Usage

Take screenshot of your wordfeud board (only works on iOS), place it in it's own directory in the `screenshots` directory i.e:

```bash
├── screenshots
│   ├── IMG_0083
│   │   └── screenshot.png
```

Run the main script to parse (with the model you copied in the installation, otherwise defaults to `eng`) and solve all the screenshots in the `screenshots` directory.

```bash
python main.py -m words-with-cheaters --solve
```

`main.py` will set up the json files for you, but you will need to validate they are accurate.

```bash
├── screenshots
│   ├── IMG_0083
│   │   ├── board.json
│   │   ├── rack.json
│   │   └── screenshot.png
```

The algorithm could be a lot faster but it generally solves for all possible words in <10 seconds for a 15x15 board with 7 tiles, including wild cards on an M2 in a single thread.

The way it works is to check every valid series on the board (a valid series includes exists if it touches another tile) for every length of word at and below the rack length as a pattern in the dictionary. It then checks if the rack can satisfy the resulting words before checking the whole board for validty and scoring the placement.

### OCR Training

To improve the OCR training, first prepare a dataset for the OCR trainer:

Set up enough `screenshot.png` files with accurate `board.json` and `rack.json` files in the `screenshots` directory. Then run the `prepare_dataset.py` script to generate the training data:

```bash
python prepare_dataset.py
```

Clone `tesstrain` next to this project:

```bash
cd .. & git clone git@github.com:tesseract-ocr/tesstrain.git
```

Then run the following command to generate the training data:

```bash
make training MODEL_NAME=words-with-cheaters \
START_MODEL=words-with-cheaters \
TESSDATA=../words-with-cheaters/dataset \
GROUND_TRUTH_DIR=../words-with-cheaters/dataset/training
```

Then copy the trained data to your tesseract data directory, e.g:

```bash
cp data/words-with-cheaters.traineddata /opt/homebrew/Cellar/tesseract/5.5.0/share/tessdata
```

And update the model in the repo (optional):

```bash
cp data/words-with-cheaters.traineddata ../words-with-cheaters/datasets/words-with-cheaters.traineddata
```

Finally, use your trained model to OCR the screenshots.

```bash
python main.py -m words-with-cheaters --solve
```

Note: The OCR will not run if there are already `board.json` and `rack.json` files in the screenshot directory.

### TODO

- [ ] Serve the solver as an API, running this on a smaller machine might show that a optimized algorithm is necessary.
- [ ] Implement a strategy algorithm to consider:
  - Word length (as there is a significant bonus to finishing as fast as possible).
  - Availability of multipliers produced by the move.
  - Holding high value tiles if their value isn't being maximized by multipliers.
- [ ] The dictionary is not complete.

- [x] Previously used wild cards should not count for points in any future moves. This will need to be encoded in the board state.
- [x] Parse a screenshot of the board and rack to get the board state and rack, this could also solve the above.
