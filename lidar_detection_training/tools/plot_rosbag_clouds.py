#!/usr/bin/env python3
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from lidar_training.rosbag_io import iter_pointcloud_frames


def middle_frame(bag_dir: Path):
    frames = list(iter_pointcloud_frames(bag_dir))
    if not frames:
        raise ValueError(f"no point clouds in {bag_dir}")
    return frames[len(frames) // 2]


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot representative corrected LiDAR frames")
    parser.add_argument("bags", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    figure, axes = plt.subplots(len(args.bags), 2, figsize=(14, 4 * len(args.bags)), squeeze=False)
    for row, bag_dir in enumerate(args.bags):
        frame = middle_frame(bag_dir)
        points = frame.points
        finite = np.isfinite(points[:, :3]).all(axis=1)
        roi = finite & (points[:, 0] >= 0) & (points[:, 0] <= 6) & (np.abs(points[:, 1]) <= 2.5)
        selected = points[roi]
        title = bag_dir.name

        bev = axes[row, 0]
        bev.scatter(selected[:, 0], selected[:, 1], c=selected[:, 2], s=2, cmap="viridis", vmin=-2, vmax=1)
        bev.set(title=f"{title} — vue de dessus", xlabel="X avant (m)", ylabel="Y gauche (m)")
        bev.set_xlim(0, 6)
        bev.set_ylim(-2.5, 2.5)
        bev.grid(alpha=0.2)

        side = axes[row, 1]
        side.scatter(selected[:, 0], selected[:, 2], c=selected[:, 3], s=2, cmap="plasma")
        side.set(title=f"{title} — vue de côté", xlabel="X avant (m)", ylabel="Z haut (m)")
        side.set_xlim(0, 6)
        side.set_ylim(-2.5, 2.5)
        side.grid(alpha=0.2)

    figure.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=180)
    print(args.output)


if __name__ == "__main__":
    main()
