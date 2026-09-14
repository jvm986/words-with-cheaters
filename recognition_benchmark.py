"""Evaluate screenshot recognition against independently labelled fixtures."""

import argparse
import base64
import hashlib
import html
import json
import platform
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pytesseract  # type: ignore[import-untyped]

from parser import Parser, CV2Image


def token(cell: Any) -> str:
    if cell.tile is not None:
        return f"{cell.tile.letter}:{cell.tile.score}"
    return cell.multiplier.name if cell.multiplier else "."


def load_fixtures(directory: Path) -> list[dict[str, Any]]:
    fixtures = []
    groups: dict[str, str] = {}
    images: dict[str, str] = {}
    ids = set()
    for path in sorted(directory.glob("*.json")):
        fixture = json.loads(path.read_text())
        if fixture["id"] in ids:
            raise ValueError("Duplicate fixture id")
        ids.add(fixture["id"])
        split = fixture["split"]
        if split not in {"baseline", "train", "validation", "test"}:
            raise ValueError(f"Invalid split in {path}")
        group = fixture["group"]
        if group in groups and groups[group] != split:
            raise ValueError(f"Game group {group} crosses splits")
        groups[group] = split
        image = (path.parent / fixture["image"]).resolve()
        digest = hashlib.sha256(image.read_bytes()).hexdigest()
        if digest in images and images[digest] != split:
            raise ValueError("Same screenshot crosses splits")
        images[digest] = split
        board, rack = fixture["board"], fixture["rack"]
        if len(board) != 15 or any(len(row) != 15 for row in board) or not 0 <= len(rack) <= 7:
            raise ValueError(f"Invalid board/rack dimensions in {path}")
        for value in [value for row in board for value in row] + rack:
            if value in {".", "DL", "TL", "DW", "TW"}:
                continue
            letter, score = value.split(":")
            if len(letter) != 1 or letter not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ?" or not score.isdigit():
                raise ValueError(f"Invalid tile {value}")
            if letter == "?" and int(score) != 0:
                raise ValueError("Rack blanks must score zero")
        if any(":" not in value for value in rack):
            raise ValueError("Rack must contain tiles only")
        if any(value.startswith("?:") for row in board for value in row):
            raise ValueError("Played blanks must have an assigned letter")
        for key in ("board_bounds", "rack_bounds"):
            if len(fixture[key]) != 4 or any(type(v) is not int for v in fixture[key]):
                raise ValueError(f"Invalid pixel coordinates in {key}")
            x1, y1, x2, y2 = fixture[key]
            if not (0 <= x1 < x2 and 0 <= y1 < y2):
                raise ValueError(f"Invalid {key}")
        decoded = cv2.imread(str(image))
        if decoded is None:
            raise ValueError(f"Unreadable image {image}")
        for key in ("board_bounds", "rack_bounds"):
            if fixture[key][2] > decoded.shape[1] or fixture[key][3] > decoded.shape[0]:
                raise ValueError(f"{key} exceeds image bounds")
        slots = fixture.get("rack_slots", rack)
        if len(slots) > 7 or [value for value in slots if value != "."] != rack:
            raise ValueError("rack_slots must match the occupied rack in order")
        fixture["rack_slots"] = slots
        fixture.update(
            image_path=str(image), image_sha256=digest, annotation_sha256=hashlib.sha256(path.read_bytes()).hexdigest()
        )
        fixtures.append(fixture)
    if not fixtures:
        raise ValueError("No fixtures found")
    return fixtures


def bounds(image: CV2Image, crop: CV2Image) -> list[int]:
    # Current parser returns views. Fail explicitly if a future adapter needs new geometry support.
    if not np.shares_memory(image, crop):
        raise ValueError("Parser crop is not a view; update benchmark geometry adapter")
    offset = crop.ctypes.data - image.ctypes.data
    y, rest = divmod(offset, image.strides[0])
    x = rest // image.strides[1]
    return [x, y, x + crop.shape[1], y + crop.shape[0]]


class MeasuredParser(Parser):
    def __init__(self) -> None:
        self.regions: dict[str, list[int]] = {}

    def crop_board_and_rack_images(self, screenshot: CV2Image) -> tuple[CV2Image, CV2Image]:
        board, rack = super().crop_board_and_rack_images(screenshot)
        self.regions = {"board_bounds": bounds(screenshot, board), "rack_bounds": bounds(screenshot, rack)}
        return board, rack


def iou(a: list[int], b: list[int]) -> float:
    intersection = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return intersection / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - intersection)


def compare(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    errors = []
    for region in ("board", "rack"):
        wanted = expected[region] if region == "board" else [expected[region]]
        got = actual[region] if region == "board" else [actual[region]]
        for r in range(max(len(wanted), len(got))):
            wr = wanted[r] if r < len(wanted) else []
            gr = got[r] if r < len(got) else []
            for c in range(max(len(wr), len(gr))):
                w = wr[c] if c < len(wr) else "<extra>"
                g = gr[c] if c < len(gr) else "<missing>"
                metrics = [f"{region}_cells"]
                if ":" in w:
                    metrics.append("occupied_tiles")
                    if w.endswith(":0"):
                        metrics.append("blanks")
                if ":" in w:
                    counts["blank_detection"][0] += int(":" in g and w.endswith(":0") == g.endswith(":0"))
                    counts["blank_detection"][1] += 1
                if w in {"DL", "TL", "DW", "TW"}:
                    metrics.append("premiums")
                for metric in metrics:
                    counts[metric][0] += int(w == g)
                    counts[metric][1] += 1
                if w != g:
                    errors.append(dict(region=region, row=r, col=c, expected=w, actual=g))
    return dict(counts=dict(counts), errors=errors, exact=not errors)


def evaluate(fixture: dict[str, Any], model: str, parser: Any = None) -> dict[str, Any]:
    parser = parser or MeasuredParser()
    start = time.perf_counter()
    result: dict[str, Any] = dict(id=fixture["id"], split=fixture["split"], group=fixture["group"])
    try:
        board, rack = parser.parse_screenshot(fixture["image_path"], model)
        actual: dict[str, Any] = dict(
            board=[[token(cell) for cell in row] for row in board.cells],
            rack=[f"{tile.letter}:{tile.score}" for tile in rack.tiles],
        )
        if len(actual["board"]) != 15 or any(len(row) != 15 for row in actual["board"]) or len(actual["rack"]) > 7:
            raise ValueError("Parser returned invalid board/rack dimensions")
        result.update(compare(fixture, actual), status="parsed", actual=actual)
    except Exception as exc:
        result.update(status="rejected", exception=f"{type(exc).__name__}: {exc}", exact=False, counts={}, errors=[])
    result["seconds"] = time.perf_counter() - start
    result["detection"] = {
        key: key in parser.regions and iou(fixture[key], parser.regions[key]) >= 0.95
        for key in ("board_bounds", "rack_bounds")
    }
    result["detected_bounds"] = parser.regions
    return result


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for result in results:
        for key, pair in result["counts"].items():
            counts[key][0] += pair[0]
            counts[key][1] += pair[1]
    return dict(
        screenshots=len(results),
        rejected=sum(r["status"] == "rejected" for r in results),
        whole_position_correct=sum(r["exact"] for r in results),
        detection_success={key: sum(r["detection"][key] for r in results) for key in ("board_bounds", "rack_bounds")},
        accuracy_on_parsed={
            key: dict(correct=a, total=b, accuracy=a / b if b else None) for key, (a, b) in counts.items()
        },
        seconds=sum(r["seconds"] for r in results),
    )


def write_report(
    fixtures: list[dict[str, Any]], results: list[dict[str, Any]], output: Path, metadata: dict[str, Any]
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    summary = {
        split: summarize([r for r in results if r["split"] == split]) for split in sorted({r["split"] for r in results})
    }
    payload = dict(metadata=metadata, summary_by_split=summary, results=results)
    (output / "results.json").write_text(json.dumps(payload, indent=2) + "\n")
    sections = []
    for fixture, result in zip(fixtures, results):
        image = cv2.imread(fixture["image_path"])
        if image is None:
            raise ValueError("Cannot render fixture image")
        # Display only the labelled game regions, omitting player names and other screenshot chrome.
        crops = []
        for region in ("board", "rack"):
            x1, y1, x2, y2 = fixture[f"{region}_bounds"]
            crop = image[y1:y2, x1:x2].copy()
            rows, cols = (15, 15) if region == "board" else (1, max(1, len(fixture["rack_slots"])))
            for error in result["errors"]:
                if error["region"] == region and error["row"] < rows and error["col"] < cols:
                    r, c = error["row"], error["col"]
                    if region == "rack":
                        occupied = [i for i, value in enumerate(fixture["rack_slots"]) if value != "."]
                        if c >= len(occupied):
                            continue
                        c = occupied[c]
                    cv2.rectangle(
                        crop,
                        (c * crop.shape[1] // cols, r * crop.shape[0] // rows),
                        ((c + 1) * crop.shape[1] // cols - 1, (r + 1) * crop.shape[0] // rows - 1),
                        (0, 0, 255),
                        4,
                    )
            ok, encoded = cv2.imencode(".png", crop)
            if not ok:
                raise ValueError("Cannot encode report crop")
            crops.append(
                f'<img alt="{region} errors outlined in red" src="data:image/png;base64,{base64.b64encode(encoded).decode()}">'
            )
        details = "\n".join(
            f"{e['region']} row {e['row']+1}, column {e['col']+1}: expected {e['expected']}, got {e['actual']}"
            for e in result["errors"]
        )
        sections.append(
            f"<section><h2>{html.escape(fixture['id'])} ({result['status']})</h2>{''.join(crops)}<pre>{html.escape(result.get('exception', details or 'No recognition mismatches.'))}</pre></section>"
        )
    page = (
        '<!doctype html><meta charset="utf-8"><title>Recognition benchmark</title><style>body{font:16px system-ui;max-width:1000px;margin:32px auto;padding:16px}img{display:block;max-width:650px;width:100%;margin:12px 0}pre{white-space:pre-wrap}section{border-top:1px solid #ccc;margin-top:32px}</style><h1>Recognition benchmark</h1><p>Red outlines mark mismatches. Coordinates below are one-based. Cell accuracy excludes rejected images; whole-position accuracy includes them. Baseline fixtures are not held-out evaluation evidence.</p><pre>'
        + html.escape(json.dumps(summary, indent=2))
        + "</pre>"
        + "".join(sections)
    )
    (output / "report.html").write_text(page)


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--fixtures", type=Path, default=Path("benchmarks/fixtures"))
    cli.add_argument("--output", type=Path, default=Path("benchmark-output"))
    cli.add_argument("--split", choices=["baseline", "train", "validation", "test"])
    cli.add_argument("--model", default="words-with-cheaters")
    args = cli.parse_args()
    fixtures = load_fixtures(args.fixtures)
    if args.split:
        fixtures = [f for f in fixtures if f["split"] == args.split]
    if not fixtures:
        cli.error("No fixtures selected")
    results = [evaluate(f, args.model) for f in fixtures]
    import os

    model_path = Path(os.environ.get("TESSDATA_PREFIX", "dataset")) / f"{args.model}.traineddata"
    try:
        tesseract_version = str(pytesseract.get_tesseract_version())
    except pytesseract.TesseractNotFoundError:
        tesseract_version = "unavailable"
    metadata = dict(
        parser_sha256=hashlib.sha256(Path(__file__).with_name("parser.py").read_bytes()).hexdigest(),
        numpy=np.__version__,
        pytesseract=pytesseract.__version__,
        model_sha256=hashlib.sha256(model_path.read_bytes()).hexdigest() if model_path.exists() else None,
        annotation_hashes={f["id"]: f["annotation_sha256"] for f in fixtures},
        model=args.model,
        python=platform.python_version(),
        opencv=cv2.__version__,
        tesseract=tesseract_version,
        fixture_hashes={f["id"]: f["image_sha256"] for f in fixtures},
    )
    write_report(fixtures, results, args.output, metadata)
    print(
        json.dumps(
            {
                split: summarize([r for r in results if r["split"] == split])
                for split in sorted({r["split"] for r in results})
            },
            indent=2,
        )
    )
    print(f"Report: {args.output / 'report.html'}")
    if any(r["status"] == "rejected" for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
