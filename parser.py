import cv2
import numpy as np
import pytesseract

from board import Board
from cell import Cell
from rack import Rack
from tile import Tile

OCR_CONFIG = "--psm 10 --oem 1"


class Parser:
    def __init__(self):
        return

    def crop_white_background(self, image, border_ratio=0.1, min_border=10):
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            max_dim = max(image.shape)
            return np.full((max_dim, max_dim), 255, dtype=np.uint8)

        x_min, y_min = np.inf, np.inf
        x_max, y_max = 0, 0

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            x_min = min(x_min, x)
            y_min = min(y_min, y)
            x_max = max(x_max, x + w)
            y_max = max(y_max, y + h)

        border_x = max(min_border, int((x_max - x_min) * border_ratio))
        border_y = max(min_border, int((y_max - y_min) * border_ratio))

        x_min = max(0, x_min - border_x)
        y_min = max(0, y_min - border_y)
        x_max = min(image.shape[1], x_max + border_x)
        y_max = min(image.shape[0], y_max + border_y)

        cropped_image = image[y_min:y_max, x_min:x_max]

        new_size = max(cropped_image.shape[:2])

        white_square = np.full((new_size, new_size), 255, dtype=np.uint8)

        y_offset = (new_size - cropped_image.shape[0]) // 2
        x_offset = (new_size - cropped_image.shape[1]) // 2

        white_square[
            y_offset : y_offset + cropped_image.shape[0],
            x_offset : x_offset + cropped_image.shape[1],
        ] = cropped_image

        return white_square

    def crop_letter_and_score_images(self, tile_image):
        height = tile_image.shape[0]
        width = tile_image.shape[1]

        if height != width:
            raise ValueError("Tile is not square")

        letter = tile_image[
            int(height * 0.15) : int(height * 0.975),
            int(width * 0.16) : int(width * 0.65),
        ]

        score = tile_image[
            int(height * 0.05) : int(height * 0.4),
            int(width * 0.66) : int(width * 0.95),
        ]

        return letter, score

    def binarize_image(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        return thresh

    def parse_tile(self, tile_image, model=None):
        ocr_config = OCR_CONFIG
        if model:
            ocr_config += f" -l {model}"

        binarized_tile_image = self.binarize_image(tile_image)
        cropped_tile_image = self.crop_white_background(binarized_tile_image)

        initial_ocr = pytesseract.image_to_string(cropped_tile_image, config=ocr_config).strip()
        if initial_ocr in ["TW", "DL", "DW", "TL"]:
            return (initial_ocr, None)

        if initial_ocr in ["", " ", "_"]:
            return ("?", 0)

        letter_image, score_image = self.crop_letter_and_score_images(cv2.bitwise_not(binarized_tile_image))

        cropped_letter_image = self.crop_white_background(letter_image)
        cropped_score_image = self.crop_white_background(score_image)

        if np.all(letter_image == 255) and np.all(score_image == 255):
            return ("?", 0)

        letter_text = (
            pytesseract.image_to_string(
                cropped_letter_image,
                config=f"{ocr_config} tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            )
            .strip()
            .upper()
        )

        if np.all(score_image == 255):
            return (letter_text, 0)

        score_text = pytesseract.image_to_string(
            cropped_score_image,
            config=f"{ocr_config} tessedit_char_whitelist=0123456789",
        ).strip()

        if score_text.isdigit():
            score_text = int(score_text)
        else:
            score_text = 0

        return (letter_text, score_text)

    def is_tile_empty(self, tile_image):
        cropped_tile_image = tile_image[
            int(tile_image.shape[0] * 0.25) : int(tile_image.shape[0] * 0.75),
            int(tile_image.shape[1] * 0.25) : int(tile_image.shape[1] * 0.75),
        ]

        if np.allclose(cropped_tile_image, cropped_tile_image[0, 0], atol=10):
            return True

        False

    def crop_tile_images(self, image):
        background_color = image[0, 0]

        bg_rows = [i for i in range(image.shape[0]) if np.allclose(image[i, :], background_color, atol=5)]

        bg_cols = [j for j in range(image.shape[1]) if np.allclose(image[:, j], background_color, atol=5)]

        def get_ranges(indices, max_index):
            ranges = []
            prev = -2
            for idx in range(max_index):
                if idx not in indices:
                    if idx != prev + 1:
                        ranges.append([idx, idx])
                    else:
                        ranges[-1][1] = idx
                    prev = idx
            return ranges

        row_ranges = get_ranges(bg_rows, image.shape[0])
        col_ranges = get_ranges(bg_cols, image.shape[1])

        tiles = []
        for r_start, r_end in row_ranges:
            row_tiles = []
            for c_start, c_end in col_ranges:
                cropped_tile = image[r_start : r_end + 1, c_start : c_end + 1]
                resized_tile = cv2.resize(
                    cropped_tile,
                    (165, 165),
                    interpolation=cv2.INTER_LINEAR,
                )
                row_tiles.append(resized_tile)
            tiles.append(row_tiles)

        return tiles

    def crop_board_and_rack_images(self, screenshot):
        header_color = screenshot[0, 0]
        board_background_color = screenshot[screenshot.shape[0] // 2, 0]

        on_background = False
        sections = []
        for i in range(len(screenshot)):
            pixel_color = screenshot[i, 0]
            is_background = np.all(pixel_color == board_background_color) or np.all(pixel_color == header_color)
            if on_background and not is_background:
                on_background = False
                sections.append(i)
            elif not on_background and is_background:
                on_background = True
                sections.append(i)

        sections.append(len(screenshot))

        board = screenshot[sections[2] : sections[3], :]
        rack = screenshot[sections[4] : sections[5], :]

        rack_height = rack.shape[0]
        rack_width = rack.shape[1]
        rack_padding = 0.01 * rack_width

        rack_height = int(rack_width / 7 + rack_padding)

        rack = rack[
            int(rack_padding) : rack_height,
            int(rack_padding) : int(rack_width - rack_padding),
        ]

        return board, rack

    def parse_screenshot(self, image_path: str, model=None):
        screenshot = cv2.imread(image_path)
        if screenshot is None:
            raise ValueError(f"Image not found at {image_path}")

        board_image, rack_image = self.crop_board_and_rack_images(screenshot)
        board_cell_images = self.crop_tile_images(board_image)
        rack_tile_images = self.crop_tile_images(rack_image)

        board_cells = [[None for _ in board_cell_images] for _ in board_cell_images[0]]

        for row_idx, _ in enumerate(board_cell_images):
            for col_idx, cell in enumerate(board_cell_images[row_idx]):
                if self.is_tile_empty(cell):
                    board_cells[row_idx][col_idx] = Cell(row_idx, col_idx)
                    continue

                letter, score = self.parse_tile(cell, model)
                board_cells[row_idx][col_idx] = Cell.from_parsed_cell(letter, score, row_idx, col_idx)

        board = Board(board_cells)

        rack_tiles = []

        for cell in rack_tile_images[0]:
            if self.is_tile_empty(cell):
                continue
            letter, score = self.parse_tile(cell, model)
            if letter:
                rack_tiles.append(Tile(letter, score))

        rack = Rack(rack_tiles)

        return board, rack
