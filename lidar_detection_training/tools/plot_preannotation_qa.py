#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

from lidar_training.canonical_io import load_canonical_sample


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a deterministic pre-annotation QA contact sheet")
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--preannotations-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    annotation_paths = sorted((args.preannotations_root / "annotations").glob("*.json"))
    payloads = [json.loads(path.read_text(encoding="utf-8")) for path in annotation_paths]
    selected = [
        _select(payloads, "1p5m", difficulty="easy", predicted=False),
        _select(payloads, "3m", difficulty="medium", predicted=False),
        _select(payloads, "5m_front", difficulty="hard", predicted=False),
        _select(payloads, "5m_front", predicted=True),
        _select(payloads, "no_ball", empty=True),
    ]

    figure, axes = plt.subplots(len(selected), 2, figsize=(12, 15), constrained_layout=True)
    for row, payload in enumerate(selected):
        sample = load_canonical_sample(args.dataset_root, payload["sample_id"])
        box = payload["boxes"][0] if payload["boxes"] else None
        center_x = box["center_xyz"][0] if box else 5.0
        center_y = box["center_xyz"][1] if box else 0.0
        crop = sample.points[
            (sample.points[:, 0] >= center_x - 0.55)
            & (sample.points[:, 0] <= center_x + 0.55)
            & (sample.points[:, 1] >= center_y - 0.55)
            & (sample.points[:, 1] <= center_y + 0.55)
            & (sample.points[:, 2] >= -1.45)
            & (sample.points[:, 2] <= -0.65)
        ]
        title = _title(payload)
        _draw(axes[row, 0], crop[:, 0], crop[:, 1], box, "top", title + " — dessus")
        _draw(axes[row, 1], crop[:, 0], crop[:, 2], box, "side", title + " — côté")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.suptitle("Contrôle visuel des préannotations — NON VALIDÉES", fontsize=16)
    figure.savefig(args.output, dpi=160)
    plt.close(figure)
    print(args.output)


def _select(payloads, token, difficulty=None, predicted=None, empty=False):
    matches = []
    for payload in payloads:
        if token not in payload["sample_id"]:
            continue
        if empty:
            if not payload["boxes"]:
                matches.append(payload)
            continue
        if not payload["boxes"]:
            continue
        attributes = payload["boxes"][0]["attributes"]
        if difficulty is not None and attributes["difficulty"] != difficulty:
            continue
        if predicted is not None and attributes["predicted_by_tracker"] != predicted:
            continue
        matches.append(payload)
    if not matches:
        raise ValueError(f"no QA sample for token={token}, difficulty={difficulty}, predicted={predicted}")
    return matches[len(matches) // 2]


def _draw(axis, x, ordinate, box, view, title):
    axis.scatter(x, ordinate, s=5, c="0.25", alpha=0.7, linewidths=0)
    if box:
        cx, cy, cz = box["center_xyz"]
        length, width, height = box["size_lwh"]
        if view == "top":
            rectangle = Rectangle((cx - length / 2, cy - width / 2), length, width)
        else:
            rectangle = Rectangle((cx - length / 2, cz - height / 2), length, height)
        rectangle.set(fill=False, edgecolor="red", linewidth=2)
        axis.add_patch(rectangle)
    axis.set_title(title, fontsize=9)
    axis.set_xlabel("X avant (m)")
    axis.set_ylabel("Y gauche (m)" if view == "top" else "Z haut (m)")
    axis.set_aspect("equal", adjustable="box")
    axis.grid(alpha=0.2)


def _title(payload):
    sample_id = payload["sample_id"]
    frame_number = sample_id.rsplit("_", 1)[-1]
    if "1p5m" in sample_id:
        label = "ballon 1,5 m"
    elif "3m" in sample_id:
        label = "ballon 3 m"
    elif "no_ball" in sample_id:
        label = "sans ballon 5 m"
    else:
        label = "ballon 5 m"
    if not payload["boxes"]:
        return f"{label} | trame {frame_number} | aucune boîte"
    attributes = payload["boxes"][0]["attributes"]
    mode = "prédit par suivi" if attributes["predicted_by_tracker"] else "mesuré"
    return (
        f"{label} | trame {frame_number} | {attributes['difficulty']} | "
        f"{attributes['num_points']} points | {mode}"
    )


if __name__ == "__main__":
    main()
