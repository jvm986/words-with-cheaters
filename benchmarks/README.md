# Recognition benchmark

Run from the repository root using Python 3.12 with the pinned requirements and Tesseract installed:

```bash
TESSDATA_PREFIX="$PWD/dataset" python recognition_benchmark.py
```

Open `benchmark-output/report.html`. The self-contained report shows the labelled board and rack crops, outlines incorrect cells in red, and lists expected/actual readings with one-based coordinates. `results.json` contains machine-readable per-fixture errors, timings, split summaries, engine versions, and model/image/annotation hashes. Output is ignored by Git. The report embeds game-region crops rather than player names and screenshot chrome.

Use `--split test`, `--fixtures PATH`, `--output PATH`, or `--model NAME` to select a run. No matching fixtures is an error. A parser exception or invalid returned dimensions is recorded as a rejected screenshot, produces a report, and exits nonzero. Recognition mismatches are reported but do not fail the command: this is a measurement baseline, not an arbitrary accuracy threshold.

## Current evidence

There is one manually checked iOS screenshot, `ios-example`, in the **baseline** split. It contains 57 occupied board tiles, seven rack tiles, 43 visible premiums, a played blank C, and a rack blank. It is not a held-out test: the existing model's training provenance is unknown. It cannot establish accuracy across devices, themes, or game states. The original image remains at `screenshots/example/screenshot.png`; fixtures refer to it rather than duplicating it.

The initial run recognized all 225 board cells and all seven rack tiles correctly, with both region detections passing. Parsing took approximately 15.5 seconds on the development machine; timing varies with hardware and load. `baseline.json` records a reproducible run's versions and hashes, with elapsed time treated as observational rather than deterministic.

## Fixture format

Each JSON file in `fixtures/` has:

- `id`: unique stable identifier.
- `image`: path relative to the JSON file.
- `split`: `baseline`, `train`, `validation`, or `test`.
- `group`: game/session identifier. Related screenshots and their transformed variants must share a group and split.
- `device`, `label_source`: provenance, including manual review and any known training overlap.
- `board_bounds`, `rack_bounds`: `[left, top, right, bottom]`, in original screenshot pixels, with exclusive right/bottom edges. Rack bounds enclose the tile row, excluding controls.
- `board`: 15 rows of 15 tokens. `.` is empty, `DL`/`TL`/`DW`/`TW` are visible empty premiums, and `A:1` is a letter with its score. `C:0` explicitly denotes a played blank assigned C. Do not infer premiums underneath occupied tiles: the baseline evaluates visible game state.
- `rack`: occupied tile tokens in left-to-right order, including `?:0` for a blank.
- `rack_slots` (optional): physical left-to-right slot labels, using `.` for empty slots. Required when the annotated rack region includes empty slots; nonempty entries must exactly match `rack`. Used for training alignment and report highlights.

Manually label from the screenshot, then have the labels checked against it. Do not save parser predictions as ground truth without reviewing every cell, score, blank and premium. Label geometry independently for new fixtures.

The loader rejects duplicate IDs, game groups crossing splits, identical image bytes crossing splits, invalid labels and invalid bounds. Different encodings/near-duplicates still require manual grouping; byte hashes cannot detect them.

## Metrics

Metrics are aggregated separately by split:

- Detection success: predicted region intersects the labelled region with IoU at least 0.95. This measures crop geometry, not letter accuracy. The current adapter reads crop coordinates from the parser's array views; a future normalising detector must expose its source-image bounds instead.
- Board and rack cell accuracy: exact token matches, including scores, with missing/extra outputs counted as errors. Rack positions are compared in occupied-tile order because the current parser discards empty slots.
- Occupied-tile accuracy: exact matches over labelled occupied board and rack tiles.
- Blank accuracy: exact matches over labelled blanks. Blank-detection accuracy also tests zero/nonzero score classification over all labelled occupied tiles. False tiles on empty cells remain visible in board-cell errors.
- Premium accuracy: exact matches over labelled visible empty premiums.
- Whole-position correctness: all board and rack tokens match; rejected images count as failures.
- Rejected count and elapsed parsing time. Cell/category accuracy is conditional on parsing succeeding, never silently counting rejected images as correct. An absent category is unmeasured, not 100% accurate.

## Grow the dataset

Aim for an initial 20–30 independently labelled screenshots covering empty/dense boards, played/rack blanks, duplicate letters, short racks, different resolutions and layouts. Split by game/session before generating crops or augmentations. Keep test screenshots out of tuning and training; use validation for iteration. Synthetic transforms can test robustness but are not additional independent screenshots.

## Training export

```bash
python prepare_dataset.py --fixtures benchmarks/fixtures --output dataset/training
```

Only `train` fixtures are exported, using annotated bounds and labels for both board and rack. The current baseline-only dataset deliberately refuses training export. Add reviewed training fixtures first; do not relabel the baseline as held out.

The output directory must be empty, preventing old crops from surviving split changes. Samples have deterministic names and matching PNG, `.gt.txt`, and `.box` files. Printed letters, nonzero scores and premiums are included; played blanks contribute their assigned letter, while rack blanks have no glyph and are skipped. Crop/label dimension disagreement fails explicitly. No train/evaluation crops are mixed automatically.
