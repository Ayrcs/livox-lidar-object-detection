import json
import pickle
from pathlib import Path

import numpy as np

from .canonical_io import load_canonical_sample, sha256_file


def evenly_spaced(items: list[dict[str, object]], count: int) -> list[dict[str, object]]:
    if count < 0:
        raise ValueError("count must be non-negative")
    if count >= len(items):
        return list(items)
    if count == 0:
        return []
    indices = np.linspace(0, len(items) - 1, count, dtype=int)
    return [items[index] for index in indices]


def annotation_to_mmdet_instance(box: dict[str, object]) -> dict[str, object]:
    center_x, center_y, center_z = (float(value) for value in box["center_xyz"])
    length, width, height = (float(value) for value in box["size_lwh"])
    return {
        "bbox_3d": [
            center_x,
            center_y,
            center_z - height / 2.0,
            length,
            width,
            height,
            float(box["yaw"]),
        ],
        "bbox_label_3d": 0,
        "num_lidar_pts": int(box["attributes"]["num_points"]),
        "bbox_3d_isvalid": True,
    }


def write_mmdet_sample(
    canonical_root: Path,
    output_root: Path,
    annotation: dict[str, object],
) -> dict[str, object]:
    sample_id = str(annotation["sample_id"])
    sample = load_canonical_sample(canonical_root, sample_id)
    points = np.ascontiguousarray(sample.points[:, :4], dtype="<f4")
    points_dir = output_root / "points"
    labels_dir = output_root / "labels"
    points_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    points_path = points_dir / f"{sample_id}.bin"
    labels_path = labels_dir / f"{sample_id}.txt"
    points.tofile(points_path)
    label_lines = []
    instances = []
    for box in annotation["boxes"]:
        instance = annotation_to_mmdet_instance(box)
        instances.append(instance)
        values = instance["bbox_3d"]
        label_lines.append(" ".join(f"{value:.9g}" for value in values) + " ball")
    labels_path.write_text("\n".join(label_lines) + ("\n" if label_lines else ""), encoding="utf-8")
    return {
        "sample_id": sample_id,
        "session_id": sample.session_id,
        "timestamp": sample.timestamp_ns,
        "lidar_points": {
            "lidar_path": points_path.relative_to(output_root).as_posix(),
            "num_pts_feats": 4,
        },
        "instances": instances,
        "point_count": len(points),
        "points_sha256": sha256_file(points_path),
        "labels_sha256": sha256_file(labels_path),
    }


def write_info_file(path: Path, entries: list[dict[str, object]]) -> None:
    payload = {
        "metainfo": {
            "categories": {"ball": 0},
            "dataset": "ball_lidar_pilot_v1",
            "info_version": "1.1",
        },
        "data_list": [
            {
                "sample_idx": entry["sample_id"],
                "token": entry["sample_id"],
                "timestamp": entry["timestamp"],
                "lidar_points": entry["lidar_points"],
                "instances": entry["instances"],
            }
            for entry in entries
        ],
    }
    with path.open("wb") as stream:
        pickle.dump(payload, stream, protocol=4)


def load_annotation(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))
