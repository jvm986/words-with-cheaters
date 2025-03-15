import logging
import os
import uuid
from collections import Counter, defaultdict
from parser import Parser

import cv2

from board import Board

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SCREENSHOTS_DIR = "screenshots"
DATASET_DIR = os.path.join("dataset", "training")
parser = Parser()

letter_counts = Counter()
all_letters = []

logging.info("Scanning screenshots to count letter occurrences...")

for screenshot_dir in os.listdir(SCREENSHOTS_DIR):
    screenshot_path = os.path.join(SCREENSHOTS_DIR, screenshot_dir, "screenshot.png")
    board = Board.load_board_from_file(os.path.join(SCREENSHOTS_DIR, screenshot_dir, "board.json"))

    screenshot_image = cv2.imread(screenshot_path)
    board_image, rack_image = parser.crop_board_and_rack_images(screenshot_image)

    board_cells = parser.crop_tile_images(board_image)
    rack_cells = parser.crop_tile_images(rack_image)

    for row_idx, row in enumerate(board_cells):
        for col_idx, cell_image in enumerate(row):
            binarized_tile_image = parser.binarize_image(cell_image)
            cell = board.get_cell(row_idx, col_idx)

            if cell.tile:
                letter_image, score_image = parser.crop_letter_and_score_images(cv2.bitwise_not(binarized_tile_image))
                cropped_letter_image = parser.crop_white_background(letter_image)
                cropped_score_image = parser.crop_white_background(score_image)

                all_letters.append((cropped_letter_image, cell.tile.letter))
                letter_counts[cell.tile.letter] += 1

                if cell.tile.score == 0:
                    continue

                all_letters.append((cropped_score_image, str(cell.tile.score)))
                letter_counts[str(cell.tile.score)] += 1
                continue

            cropped_tile_image = parser.crop_white_background(binarized_tile_image)
            if cell.multiplier:
                all_letters.append((cropped_tile_image, cell.multiplier.name))
                letter_counts[cell.multiplier.name] += 1
                continue

            if board.is_cell_middle(row_idx, col_idx):
                all_letters.append((cropped_tile_image, "Ø"))
                letter_counts["Ø"] += 1

if letter_counts:
    min_letter_count = max(min(letter_counts.values()), 100)
    logging.info(f"Adjusted minimum letter count: {min_letter_count}")
else:
    min_letter_count = 100
    logging.warning("No letters found in dataset. Nothing to save.")

logging.info("Letter frequencies before saving:")
for letter, count in letter_counts.items():
    logging.info(f"{letter}: {count}")

saved_counts = defaultdict(int)


def write_image_and_gt(image, text):
    """Save the image and ground truth only if below the minimum threshold."""
    if saved_counts[text] >= min_letter_count:
        logging.debug(f"Skipping '{text}' (limit reached: {min_letter_count})")
        return

    id = uuid.uuid4()
    image_path = os.path.join(DATASET_DIR, f"{text}_{id}.png")
    gt_text_path = os.path.join(DATASET_DIR, f"{text}_{id}.gt.txt")
    box_path = os.path.join(DATASET_DIR, f"{text}_{id}.box")

    cv2.imwrite(image_path, image)

    with open(gt_text_path, "w") as f:
        f.write(text)

    h, w = image.shape[:2]
    box_data = f"{text} 0 0 {w} {h} 0\n"
    with open(box_path, "w") as f:
        f.write(box_data)

    saved_counts[text] += 1
    logging.debug(f"Saved '{text}' (Total: {saved_counts[text]}/{min_letter_count})")


logging.info("Saving images to dataset...")
for image, text in all_letters:
    write_image_and_gt(image, text)

logging.info("Processing complete.")
