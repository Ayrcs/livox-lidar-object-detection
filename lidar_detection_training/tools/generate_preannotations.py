#!/usr/bin/env python3
import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import yaml

from lidar_training.annotations import box_to_preannotation, validate_annotation, write_annotation
from lidar_training.baseline import BaselineConfig, detect_ball_candidates
from lidar_training.canonical_io import load_canonical_sample
from lidar_training.geometry import points_in_oriented_box
from lidar_training.tracking import BallTracker, TrackerConfig
from lidar_training.visibility import FloorFitConfig, fit_floor_plane, heights_above_plane


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate explicitly unreviewed geometric pre-annotations")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--include-tracker-predictions",
        action="store_true",
        help="Keep boxes extrapolated without a measured candidate (disabled by default)",
    )
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    ground_truth = yaml.safe_load(Path(config["ground_truth_config"]).read_text(encoding="utf-8"))
    detector_config = _detector_config(config["detector"])
    tracker_config = TrackerConfig(**config["tracker"])
    dataset_root = Path(config["dataset_root"])
    annotations_dir = args.output_dir / "annotations"
    entries: list[dict[str, object]] = []
    counters: Counter[str] = Counter()

    for session in ground_truth["sessions"]:
        tracker = BallTracker(tracker_config)
        sample_paths = sorted((dataset_root / "metadata").glob(f"{session['session_id']}_*.json"))
        for metadata_path in sample_paths:
            sample = load_canonical_sample(dataset_root, metadata_path.stem)
            candidates = detect_ball_candidates(sample.points, detector_config)
            tracked = tracker.update(candidates, sample.timestamp_ns)
            boxes: list[dict[str, object]] = []
            is_tracker_prediction = bool(
                tracked is not None and tracked.attributes.get("predicted", False)
            )
            if tracked is not None and (args.include_tracker_predictions or not is_tracker_prediction):
                floor = fit_floor_plane(sample.points, detector_config.floor_fit)
                heights = heights_above_plane(sample.points, floor)
                physical_box_count = int(points_in_oriented_box(sample.points, tracked).sum())
                target_mask = points_in_oriented_box(sample.points, tracked) & (heights >= 0.02)
                target_mask &= heights <= 0.24
                target_count = int(target_mask.sum())
                boxes.append(
                    box_to_preannotation(
                        tracked,
                        annotation_id=f"{sample.sample_id}_ball_0",
                        num_points=target_count,
                        num_points_in_box=physical_box_count,
                    )
                )
                counters[f"difficulty_{boxes[0]['attributes']['difficulty']}"] += 1
                counters["predicted_boxes"] += int(boxes[0]["attributes"]["predicted_by_tracker"])
                counters["boxes"] += 1
            else:
                counters["empty_samples"] += 1
                counters["excluded_tracker_predictions"] += int(is_tracker_prediction)
            path, digest = write_annotation(
                annotations_dir,
                sample.sample_id,
                sample.frame_id,
                boxes,
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
            errors = validate_annotation(payload)
            if errors:
                raise ValueError(f"{path}: {errors}")
            entries.append(
                {
                    "sample_id": sample.sample_id,
                    "annotation_path": path.relative_to(args.output_dir).as_posix(),
                    "annotation_sha256": digest,
                    "box_count": len(boxes),
                }
            )

    manifest = {
        "schema_version": 1,
        "source": (
            "geometric_baseline_tracker_with_predictions"
            if args.include_tracker_predictions
            else "geometric_baseline_tracker_measured_only"
        ),
        "tracker_predictions_included": args.include_tracker_predictions,
        "review_status": "unreviewed",
        "sample_count": len(entries),
        "summary": dict(sorted(counters.items())),
        "annotations": sorted(entries, key=lambda item: item["sample_id"]),
    }
    manifest_path = args.output_dir / "preannotation_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(manifest_path)
    print(json.dumps(manifest["summary"], indent=2, sort_keys=True))


def _detector_config(values: dict[str, object]) -> BaselineConfig:
    copied = dict(values)
    copied["floor_fit"] = FloorFitConfig(**_tuples(copied["floor_fit"]))
    return BaselineConfig(**_tuples(copied))


def _tuples(values: dict[str, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in values.items():
        if isinstance(value, list):
            result[key] = tuple(tuple(item) if isinstance(item, list) else item for item in value)
        else:
            result[key] = value
    return result


if __name__ == "__main__":
    main()
