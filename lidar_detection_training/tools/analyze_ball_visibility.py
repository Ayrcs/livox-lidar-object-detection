#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path

import numpy as np
import yaml

from lidar_training.rosbag_io import iter_pointcloud_frames
from lidar_training.visibility import (
    FloorFitConfig,
    count_target_returns,
    fit_floor_plane,
    summarize_counts,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Reproduce the initial ball visibility measurements")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--bags-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    floor_config = FloorFitConfig(**_tuple_ranges(config["floor_fit"]))
    roi_config = _tuple_ranges(config["target_roi"])
    results = {"schema_version": 1, "config": str(args.config), "sessions": []}
    frame_rows: list[dict[str, object]] = []

    for session in config["sessions"]:
        frames = list(iter_pointcloud_frames(args.bags_root / session["session_id"]))
        all_points = np.concatenate([frame.points for frame in frames])
        floor = fit_floor_plane(all_points, floor_config)
        counts: list[int] = []
        intensities: list[float] = []
        for frame_index, frame in enumerate(frames):
            count, selected = count_target_returns(
                frame.points,
                floor,
                tuple(session["center_xy_m"]),
                **roi_config,
            )
            counts.append(count)
            intensities.extend(selected[:, 3].tolist())
            frame_rows.append(
                {
                    "session_id": session["session_id"],
                    "frame_index": frame_index,
                    "header_timestamp_ns": frame.header_timestamp_ns,
                    "return_count": count,
                }
            )
        summary = summarize_counts(np.asarray(counts))
        summary.update(
            {
                "session_id": session["session_id"],
                "label": session["label"],
                "distance_m": session["distance_m"],
                "negative": session["negative"],
                "center_xy_m": session["center_xy_m"],
                "floor_plane_abc": floor.tolist(),
                "intensity_mean": float(np.mean(intensities)) if intensities else None,
                "intensity_std": float(np.std(intensities)) if intensities else None,
            }
        )
        results["sessions"].append(summary)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = args.output_dir / "metrics.json"
    counts_path = args.output_dir / "frame_counts.csv"
    metrics_path.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with counts_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=frame_rows[0].keys())
        writer.writeheader()
        writer.writerows(frame_rows)
    print(metrics_path)
    print(counts_path)


def _tuple_ranges(values: dict[str, object]) -> dict[str, object]:
    return {
        key: tuple(value) if isinstance(value, list) and len(value) == 2 else value
        for key, value in values.items()
    }


if __name__ == "__main__":
    main()
