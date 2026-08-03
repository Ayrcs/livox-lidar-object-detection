#!/usr/bin/env python3
import argparse
import json
from collections import Counter
from pathlib import Path

from lidar_training.annotations import validate_annotation
from lidar_training.canonical_io import load_canonical_sample, sha256_file
from lidar_training.geometry import points_in_oriented_box
from lidar_training.types import Box3D


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate pre-annotations against canonical samples")
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--preannotations-root", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    manifest_path = args.preannotations_root / "preannotation_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    counters: Counter[str] = Counter()
    seen: set[str] = set()

    for entry in manifest.get("annotations", []):
        sample_id = entry["sample_id"]
        if sample_id in seen:
            errors.append(f"{sample_id}: duplicate manifest entry")
            continue
        seen.add(sample_id)
        path = args.preannotations_root / entry["annotation_path"]
        if not path.is_file():
            errors.append(f"{sample_id}: missing annotation file")
            continue
        if sha256_file(path) != entry["annotation_sha256"]:
            errors.append(f"{sample_id}: annotation checksum mismatch")
        payload = json.loads(path.read_text(encoding="utf-8"))
        errors.extend(f"{sample_id}: {error}" for error in validate_annotation(payload))
        sample = load_canonical_sample(args.dataset_root, sample_id)
        if payload.get("sample_id") != sample_id:
            errors.append(f"{sample_id}: payload sample_id mismatch")
        if payload.get("frame_id") != sample.frame_id:
            errors.append(f"{sample_id}: frame_id mismatch")
        if entry.get("box_count") != len(payload.get("boxes", [])):
            errors.append(f"{sample_id}: box_count mismatch")
        counters["samples"] += 1
        counters["boxes"] += len(payload.get("boxes", []))
        for box_payload in payload.get("boxes", []):
            box = Box3D(
                class_name=box_payload["class_name"],
                center_xyz=tuple(box_payload["center_xyz"]),
                size_lwh=tuple(box_payload["size_lwh"]),
                yaw=float(box_payload["yaw"]),
            )
            actual_count = int(points_in_oriented_box(sample.points, box).sum())
            recorded_count = box_payload["attributes"]["num_points_in_box"]
            if actual_count != recorded_count:
                errors.append(
                    f"{sample_id}: num_points_in_box {recorded_count} != {actual_count}"
                )

    metadata_ids = {path.stem for path in (args.dataset_root / "metadata").glob("*.json")}
    missing = sorted(metadata_ids - seen)
    extra = sorted(seen - metadata_ids)
    errors.extend(f"{sample_id}: canonical sample has no annotation" for sample_id in missing)
    errors.extend(f"{sample_id}: annotation has no canonical sample" for sample_id in extra)
    if manifest.get("sample_count") != counters["samples"]:
        errors.append("manifest sample_count mismatch")

    report = {
        "schema_version": 1,
        "status": "valid" if not errors else "invalid",
        "sample_count": counters["samples"],
        "box_count": counters["boxes"],
        "error_count": len(errors),
        "errors": errors,
        "preannotation_manifest_sha256": sha256_file(manifest_path),
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
