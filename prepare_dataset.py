"""Export Tesseract crops from labelled training fixtures (never evaluation fixtures)."""

import argparse
import hashlib
from pathlib import Path
from typing import Iterator

import cv2

from parser import CV2Image, Parser
from recognition_benchmark import load_fixtures


def tile_samples(parser: Parser, image: CV2Image, label: str) -> Iterator[tuple[CV2Image, str]]:
    binary = parser.binarize_image(image)
    if ":" in label:
        letter, score = label.split(":")
        # A rack blank has no printed glyph to train. Played blanks still have a letter.
        if letter == "?":
            return
        letter_image, score_image = parser.crop_letter_and_score_images(cv2.bitwise_not(binary))
        yield parser.crop_white_background(letter_image), letter
        if score != "0":
            yield parser.crop_white_background(score_image), score
    elif label != ".":
        yield parser.crop_white_background(binary), label


def prepare(fixtures_dir: Path, output: Path) -> int:
    fixtures = load_fixtures(fixtures_dir)
    training = [fixture for fixture in fixtures if fixture["split"] == "train"]
    if not training:
        raise ValueError("No train fixtures. Baseline, validation and test fixtures are excluded from training.")
    # A fresh directory prevents stale crops from silently leaking across split changes.
    if output.exists() and any(output.iterdir()):
        raise ValueError("Training output must be empty; choose a new output directory")
    parser = Parser()
    samples: list[tuple[CV2Image, str]] = []
    for fixture in training:
        image = cv2.imread(fixture["image_path"])
        if image is None:
            raise ValueError(f"Cannot read {fixture['id']}")
        for region in ("board", "rack"):
            x1, y1, x2, y2 = fixture[f"{region}_bounds"]
            cells = parser.crop_tile_images(image[y1:y2, x1:x2])
            labels = fixture[region] if region == "board" else [fixture["rack_slots"]]
            if len(cells) != len(labels) or any(len(row) != len(label_row) for row, label_row in zip(cells, labels)):
                raise ValueError(f"Crop/label dimensions disagree for {fixture['id']} {region}")
            for row, label_row in zip(cells, labels):
                for cell, label in zip(row, label_row):
                    samples.extend(tile_samples(parser, cell, label))
    output.mkdir(parents=True, exist_ok=True)
    for index, (crop, label) in enumerate(samples):
        digest = hashlib.sha256(crop.tobytes() + label.encode()).hexdigest()[:12]
        stem = output / f"{index:06d}_{digest}"
        if not cv2.imwrite(str(stem) + ".png", crop):
            raise ValueError("Failed writing training crop")
        Path(str(stem) + ".gt.txt").write_text(label + "\n")
        height, width = crop.shape[:2]
        Path(str(stem) + ".box").write_text(f"{label} 0 0 {width} {height} 0\n")
    return len(samples)


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--fixtures", type=Path, default=Path("benchmarks/fixtures"))
    cli.add_argument("--output", type=Path, default=Path("dataset/training"))
    args = cli.parse_args()
    print(f"Wrote {prepare(args.fixtures, args.output)} training crops to {args.output}")


if __name__ == "__main__":
    main()
