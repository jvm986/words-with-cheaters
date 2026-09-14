import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np

from recognition_benchmark import compare, evaluate, iou, load_fixtures, summarize, write_report
from prepare_dataset import prepare, tile_samples
from parser import Parser


class BenchmarkTests(unittest.TestCase):
    def test_metrics_distinguish_tile_blank_and_premium_errors(self):
        expected = dict(board=[["A:1", "C:0", "TW", "."]], rack=["?:0", "E:1"])
        actual = dict(board=[["A:0", "C:1", "DW", "."]], rack=["?:0"])
        result = compare(expected, actual)
        self.assertEqual(result["counts"]["board_cells"], [1, 4])
        self.assertEqual(result["counts"]["occupied_tiles"], [1, 4])
        self.assertEqual(result["counts"]["blanks"], [1, 2])
        self.assertEqual(result["counts"]["premiums"], [0, 1])
        self.assertEqual(len(result["errors"]), 4)
        self.assertFalse(result["exact"])

    def test_extra_tiles_count_as_errors(self):
        result = compare(dict(board=[["."]], rack=[]), dict(board=[["."]], rack=["A:1"]))
        self.assertEqual(result["counts"]["rack_cells"], [0, 1])
        self.assertFalse(result["exact"])

    def test_rejection_is_not_perfect_accuracy(self):
        class BrokenParser:
            regions = {}

            def parse_screenshot(self, *_):
                raise ValueError("could not locate board")

        fixture = dict(
            id="bad", split="test", group="g", image_path="unused", board_bounds=[0, 0, 1, 1], rack_bounds=[0, 0, 1, 1]
        )
        result = evaluate(fixture, "unused", BrokenParser())
        summary = summarize([result])
        self.assertEqual(summary["rejected"], 1)
        self.assertEqual(summary["whole_position_correct"], 0)
        self.assertEqual(summary["accuracy_on_parsed"], {})
        self.assertEqual(summary["detection_success"]["board_bounds"], 0)

    def test_iou(self):
        self.assertEqual(iou([0, 0, 10, 10], [0, 0, 10, 10]), 1)
        self.assertEqual(iou([0, 0, 10, 10], [10, 10, 20, 20]), 0)
        self.assertAlmostEqual(iou([0, 0, 10, 10], [0, 0, 5, 10]), 0.5)

    def test_real_fixture_loads(self):
        fixture = load_fixtures(Path("benchmarks/fixtures"))[0]
        self.assertEqual(fixture["split"], "baseline")
        self.assertEqual(fixture["board"][2][6], "C:0")
        self.assertEqual(fixture["rack"][5], "?:0")

    def test_group_and_image_split_leakage_rejected(self):
        original = json.loads(Path("benchmarks/fixtures/ios-example.json").read_text())
        original["image"] = str(Path("screenshots/example/screenshot.png").resolve())
        for same_group in (True, False):
            with self.subTest(same_group=same_group), tempfile.TemporaryDirectory() as tmp:
                first = dict(original, split="train")
                second = dict(original, id="second", split="test", group=original["group"] if same_group else "other")
                Path(tmp, "a.json").write_text(json.dumps(first))
                Path(tmp, "b.json").write_text(json.dumps(second))
                with self.assertRaisesRegex(ValueError, "crosses splits"):
                    load_fixtures(Path(tmp))

    def test_training_excludes_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "No train fixtures"):
                prepare(Path("benchmarks/fixtures"), Path(tmp) / "output")

    def test_rack_samples_exported_without_evaluation_leakage(self):
        image = np.zeros((165, 165, 3), dtype=np.uint8)
        train = dict(
            id="train",
            split="train",
            image_path="unused",
            board_bounds=[0, 0, 1, 1],
            rack_bounds=[0, 0, 1, 1],
            board=[["."]],
            rack=["Z:10"],
            rack_slots=["Z:10", "."],
        )
        evaluation = dict(train, id="heldout", split="test")
        with tempfile.TemporaryDirectory() as tmp, patch(
            "prepare_dataset.load_fixtures", return_value=[train, evaluation]
        ), patch("prepare_dataset.cv2.imread", return_value=image), patch.object(
            Parser, "crop_tile_images", side_effect=[[[image]], [[image, image]]]
        ):
            output = Path(tmp) / "training"
            self.assertEqual(prepare(Path(tmp), output), 2)
            self.assertEqual(sorted(p.read_text().strip() for p in output.glob("*.gt.txt")), ["10", "Z"])
            with self.assertRaisesRegex(ValueError, "must be empty"):
                prepare(Path(tmp), output)

    def test_blank_training(self):
        image = np.zeros((165, 165, 3), dtype=np.uint8)
        self.assertEqual(list(tile_samples(Parser(), image, "?:0")), [])
        self.assertEqual([label for _, label in tile_samples(Parser(), image, "C:0")], ["C"])

    def test_visual_report_contains_error_location_and_embedded_image(self):
        fixture = load_fixtures(Path("benchmarks/fixtures"))[0]
        actual = dict(board=[list(row) for row in fixture["board"]], rack=list(fixture["rack"]))
        actual["board"][2][6] = "G:3"
        result = dict(
            compare(fixture, actual),
            id=fixture["id"],
            split="baseline",
            status="parsed",
            seconds=0,
            detection=dict(board_bounds=True, rack_bounds=True),
        )
        with tempfile.TemporaryDirectory() as tmp:
            write_report([fixture], [result], Path(tmp), {})
            report = Path(tmp, "report.html").read_text()
            self.assertIn("row 3, column 7: expected C:0, got G:3", report)
            self.assertIn("data:image/png;base64,", report)
            self.assertEqual(
                json.loads(Path(tmp, "results.json").read_text())["summary_by_split"]["baseline"][
                    "whole_position_correct"
                ],
                0,
            )
