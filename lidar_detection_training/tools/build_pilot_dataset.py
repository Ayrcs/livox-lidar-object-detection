#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import yaml

from lidar_training.canonical_io import sha256_file
from lidar_training.pilot_dataset import (
    evenly_spaced,
    load_annotation,
    write_info_file,
    write_mmdet_sample,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the measured-only MMDetection3D pilot dataset")
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    canonical_root = Path(config["canonical_root"])
    annotations_root = Path(config["annotations_root"])
    output_root = Path(config["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    negative_sessions = set(config["negative_sessions"])
    all_entries: dict[str, dict[str, object]] = {}
    split_entries: dict[str, list[dict[str, object]]] = {}

    for split_name, split_config in config["splits"].items():
        entries = []
        for session_id in split_config["sessions"]:
            paths = sorted((annotations_root / "annotations").glob(f"{session_id}_*.json"))
            for path in paths:
                annotation = load_annotation(path)
                is_negative = session_id in negative_sessions
                if not annotation["boxes"] and not is_negative:
                    if split_config["positive_empty_policy"] == "exclude":
                        continue
                    raise ValueError(f"unsupported positive_empty_policy for {split_name}")
                sample_id = annotation["sample_id"]
                if sample_id not in all_entries:
                    all_entries[sample_id] = write_mmdet_sample(
                        canonical_root, output_root, annotation
                    )
                entries.append(all_entries[sample_id])
        split_entries[split_name] = entries
        write_info_file(output_root / f"ball_infos_{split_name}.pkl", entries)
        image_set = output_root / "ImageSets"
        image_set.mkdir(exist_ok=True)
        (image_set / f"{split_name}.txt").write_text(
            "\n".join(str(entry["sample_id"]) for entry in entries) + "\n",
            encoding="utf-8",
        )

    train_positive = [entry for entry in split_entries["train"] if entry["instances"]]
    train_negative = [entry for entry in split_entries["train"] if not entry["instances"]]
    overfit = evenly_spaced(train_positive, config["overfit_subset"]["positive_samples"])
    overfit += evenly_spaced(train_negative, config["overfit_subset"]["negative_samples"])
    overfit.sort(key=lambda entry: str(entry["sample_id"]))
    write_info_file(output_root / "ball_infos_overfit.pkl", overfit)
    (output_root / "ImageSets" / "overfit.txt").write_text(
        "\n".join(str(entry["sample_id"]) for entry in overfit) + "\n",
        encoding="utf-8",
    )

    split_summary = {}
    for name, entries in {**split_entries, "overfit": overfit}.items():
        split_summary[name] = {
            "samples": len(entries),
            "positive_samples": sum(bool(entry["instances"]) for entry in entries),
            "negative_samples": sum(not entry["instances"] for entry in entries),
            "sessions": sorted({str(entry["session_id"]) for entry in entries}),
            "info_sha256": sha256_file(output_root / f"ball_infos_{name}.pkl"),
        }
    manifest = {
        "schema_version": 1,
        "dataset_id": config["dataset_id"],
        "status": "pilot_unreviewed_measured_preannotations",
        "point_features": config["point_features"],
        "box_z_convention": config["mmdet3d_box_z_convention"],
        "splits": split_summary,
        "limitations": [
            "Static indoor concrete scene only",
            "Machine preannotations accepted only for pilot training",
            "Validation holds out distance but not location or recording day",
            "No independent test set is possible with four sessions",
        ],
    }
    manifest_path = output_root / "pilot_dataset_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(manifest_path)
    print(json.dumps(split_summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
