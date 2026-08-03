#!/usr/bin/env python3
import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np
import yaml

from lidar_training.baseline import BaselineConfig, detect_ball_candidates
from lidar_training.canonical_io import load_canonical_sample
from lidar_training.tracking import BallTracker, TrackerConfig
from lidar_training.visibility import FloorFitConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the pilot geometric baseline")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    ground_truth = yaml.safe_load(Path(config["ground_truth_config"]).read_text(encoding="utf-8"))
    detector_config = _detector_config(config["detector"])
    tracker_config = TrackerConfig(**config["tracker"])
    dataset_root = Path(config["dataset_root"])
    match_distance = float(config["match_distance_m"])
    rows: list[dict[str, object]] = []
    session_metrics: list[dict[str, object]] = []

    for session in ground_truth["sessions"]:
        sample_paths = sorted((dataset_root / "metadata").glob(f"{session['session_id']}_*.json"))
        target_xy = np.asarray(session["center_xy_m"], dtype=np.float64)
        target_present = not bool(session["negative"])
        tracker = BallTracker(tracker_config)
        candidate_matches = candidate_false = tracked_matches = tracked_false = 0
        tracked_errors: list[float] = []
        latencies_ms: list[float] = []
        timestamps: list[int] = []

        for frame_index, metadata_path in enumerate(sample_paths):
            sample = load_canonical_sample(dataset_root, metadata_path.stem)
            timestamps.append(sample.timestamp_ns)
            started = time.perf_counter()
            candidates = detect_ball_candidates(sample.points, detector_config)
            latencies_ms.append((time.perf_counter() - started) * 1000)
            candidate_distances = [_xy_error(item.center_xyz, target_xy) for item in candidates]
            candidate_matched = target_present and bool(candidate_distances) and min(candidate_distances) <= match_distance
            candidate_matches += int(candidate_matched)
            candidate_false += len(candidates) - int(candidate_matched)

            tracked = tracker.update(candidates, sample.timestamp_ns)
            tracked_error = _xy_error(tracked.center_xyz, target_xy) if tracked is not None else None
            tracked_matched = target_present and tracked_error is not None and tracked_error <= match_distance
            tracked_matches += int(tracked_matched)
            tracked_false += int(tracked is not None and not tracked_matched)
            if tracked_matched:
                tracked_errors.append(float(tracked_error))
            rows.append(
                {
                    "session_id": session["session_id"],
                    "frame_index": frame_index,
                    "timestamp_ns": sample.timestamp_ns,
                    "candidate_count": len(candidates),
                    "candidate_matched": candidate_matched,
                    "tracked_output": tracked is not None,
                    "tracked_matched": tracked_matched,
                    "tracked_predicted": bool(tracked and tracked.attributes["predicted"]),
                    "tracked_xy_error_m": tracked_error,
                    "detector_latency_ms": latencies_ms[-1],
                }
            )

        frame_count = len(sample_paths)
        duration_s = (max(timestamps) - min(timestamps)) / 1_000_000_000 if len(timestamps) > 1 else 0.0
        session_metrics.append(
            {
                "session_id": session["session_id"],
                "label": session["label"],
                "target_present": target_present,
                "frame_count": frame_count,
                "duration_s": duration_s,
                "candidate_recall": candidate_matches / frame_count if target_present else None,
                "candidate_false_per_frame": candidate_false / frame_count,
                "tracked_recall": tracked_matches / frame_count if target_present else None,
                "tracked_false_per_frame": tracked_false / frame_count,
                "tracked_false_per_minute": tracked_false / duration_s * 60 if duration_s else None,
                "tracked_xy_error_median": float(np.median(tracked_errors)) if tracked_errors else None,
                "tracked_xy_error_p95": float(np.percentile(tracked_errors, 95)) if tracked_errors else None,
                "detector_latency_ms_mean": float(np.mean(latencies_ms)),
                "detector_latency_ms_p95": float(np.percentile(latencies_ms, 95)),
            }
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = args.output_dir / "metrics.json"
    predictions_path = args.output_dir / "predictions.csv"
    metrics_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "experiment_name": config["experiment_name"],
                "limitations": [
                    "Detector parameters and evaluation use the same four static feasibility sessions.",
                    "The evaluated ROI is limited to the measured front corridor |Y| <= 0.8 m.",
                    "No moving ball, moving robot, occlusion, grass, or hard distractor is represented.",
                ],
                "sessions": session_metrics,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    with predictions_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(metrics_path)
    print(predictions_path)


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


def _xy_error(center_xyz: tuple[float, float, float], target_xy: np.ndarray) -> float:
    return float(np.linalg.norm(np.asarray(center_xyz[:2]) - target_xy))


if __name__ == "__main__":
    main()
