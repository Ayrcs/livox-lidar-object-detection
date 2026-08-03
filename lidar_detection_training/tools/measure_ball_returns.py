#!/usr/bin/env python3
import argparse
import csv
from dataclasses import asdict
from pathlib import Path

from lidar_training.io import load_sample
from lidar_training.measurements import measure_box_returns


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure LiDAR returns inside annotated ball boxes")
    parser.add_argument("samples", type=Path, help="Directory containing canonical .npz samples and .json sidecars")
    parser.add_argument("--output", type=Path, default=Path("ball_returns.csv"))
    args = parser.parse_args()
    rows = []
    for path in sorted(args.samples.glob("*.npz")):
        sample = load_sample(path)
        for index, box in enumerate(sample.boxes):
            if box.class_name != "ball":
                continue
            row = asdict(measure_box_returns(sample.points, box))
            row.update(sample_id=sample.sample_id, session_id=sample.session_id, box_index=index)
            rows.append(row)
    fields = ["sample_id", "session_id", "box_index", "num_points", "distance_m", "azimuth_deg",
              "intensity_mean", "intensity_std", "cluster_size_xyz_m"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} ball measurements to {args.output}")


if __name__ == "__main__":
    main()
