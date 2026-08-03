#!/usr/bin/env python3
import argparse
import json
import pickle
from pathlib import Path

import numpy as np

from lidar_training.canonical_io import sha256_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the MMDetection3D pilot dataset")
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    errors: list[str] = []
    splits = {}

    for name in ("train", "val_distance_holdout", "overfit"):
        path = args.dataset_root / f"ball_infos_{name}.pkl"
        with path.open("rb") as stream:
            payload = pickle.load(stream)
        entries = payload["data_list"]
        sample_ids = []
        sessions = set()
        positive = 0
        for entry in entries:
            sample_id = str(entry["sample_idx"])
            sample_ids.append(sample_id)
            sessions.add(sample_id.rsplit("_", 1)[0])
            point_path = args.dataset_root / entry["lidar_points"]["lidar_path"]
            if not point_path.is_file():
                errors.append(f"{name}/{sample_id}: missing point file")
                continue
            if point_path.stat().st_size % (4 * 4) != 0:
                errors.append(f"{name}/{sample_id}: invalid float32 Nx4 file size")
            for instance in entry["instances"]:
                positive += 1
                box = np.asarray(instance["bbox_3d"], dtype=float)
                if box.shape != (7,) or not np.isfinite(box).all():
                    errors.append(f"{name}/{sample_id}: invalid box values")
                elif np.any(box[3:6] <= 0):
                    errors.append(f"{name}/{sample_id}: non-positive box dimensions")
                if instance["bbox_label_3d"] != 0:
                    errors.append(f"{name}/{sample_id}: unexpected class index")
                if instance["num_lidar_pts"] <= 0:
                    errors.append(f"{name}/{sample_id}: box without measured target return")
        if len(sample_ids) != len(set(sample_ids)):
            errors.append(f"{name}: duplicate sample identifiers")
        splits[name] = {
            "samples": len(entries),
            "positive_boxes": positive,
            "negative_samples": sum(not entry["instances"] for entry in entries),
            "sessions": sorted(sessions),
            "sample_ids": set(sample_ids),
            "info_sha256": sha256_file(path),
        }

    overlap = splits["train"]["sample_ids"] & splits["val_distance_holdout"]["sample_ids"]
    if overlap:
        errors.append(f"train/validation sample overlap: {len(overlap)}")
    train_sessions = set(splits["train"]["sessions"])
    val_sessions = set(splits["val_distance_holdout"]["sessions"])
    if train_sessions & val_sessions:
        errors.append("train/validation session overlap")
    if not splits["overfit"]["sample_ids"].issubset(splits["train"]["sample_ids"]):
        errors.append("overfit split is not a subset of train")

    public_splits = {
        name: {key: value for key, value in values.items() if key != "sample_ids"}
        for name, values in splits.items()
    }
    report = {
        "schema_version": 1,
        "status": "valid" if not errors else "invalid",
        "error_count": len(errors),
        "errors": errors,
        "splits": public_splits,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
