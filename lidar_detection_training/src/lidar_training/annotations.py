import hashlib
import json
from pathlib import Path

import numpy as np

from .types import Box3D


ANNOTATION_SCHEMA_VERSION = 1
ALLOWED_CLASSES = {"ball", "unitree_g1"}


def difficulty_from_points(num_points: int) -> str:
    if num_points < 3:
        return "hard"
    if num_points < 10:
        return "medium"
    return "easy"


def write_annotation(
    annotation_dir: Path,
    sample_id: str,
    frame_id: str,
    boxes: list[dict[str, object]],
    review_status: str = "unreviewed",
) -> tuple[Path, str]:
    annotation_dir.mkdir(parents=True, exist_ok=True)
    path = annotation_dir / f"{sample_id}.json"
    payload = {
        "schema_version": ANNOTATION_SCHEMA_VERSION,
        "sample_id": sample_id,
        "frame_id": frame_id,
        "review_status": review_status,
        "boxes": boxes,
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return path, _sha256(path)


def box_to_preannotation(
    box: Box3D,
    annotation_id: str,
    num_points: int,
    num_points_in_box: int,
) -> dict[str, object]:
    return {
        "annotation_id": annotation_id,
        "class_name": box.class_name,
        "center_xyz": list(box.center_xyz),
        "size_lwh": list(box.size_lwh),
        "yaw": box.yaw,
        "source": str(box.attributes.get("source", "unknown")),
        "review_status": "unreviewed",
        "attributes": {
            "occluded": "unknown",
            "truncated": False,
            "moving": "unknown",
            "difficulty": difficulty_from_points(num_points),
            "num_points": num_points,
            "num_points_in_box": num_points_in_box,
            "predicted_by_tracker": bool(box.attributes.get("predicted", False)),
            "track_hits": int(box.attributes.get("track_hits", 0)),
            "track_misses": int(box.attributes.get("track_misses", 0)),
        },
    }


def validate_annotation(payload: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != ANNOTATION_SCHEMA_VERSION:
        errors.append("unsupported schema_version")
    if not payload.get("sample_id"):
        errors.append("sample_id is required")
    if not payload.get("frame_id"):
        errors.append("frame_id is required")
    if payload.get("review_status") not in {"unreviewed", "reviewed", "rejected"}:
        errors.append("invalid sample review_status")
    boxes = payload.get("boxes")
    if not isinstance(boxes, list):
        return errors + ["boxes must be a list"]
    for index, box in enumerate(boxes):
        prefix = f"boxes[{index}]"
        if not isinstance(box, dict):
            errors.append(f"{prefix}: box must be an object")
            continue
        if not box.get("annotation_id"):
            errors.append(f"{prefix}: annotation_id is required")
        if box.get("review_status") not in {"unreviewed", "reviewed", "rejected"}:
            errors.append(f"{prefix}: invalid review_status")
        if box.get("class_name") not in ALLOWED_CLASSES:
            errors.append(f"{prefix}: unknown class")
        try:
            parsed = Box3D(
                class_name=box["class_name"],
                center_xyz=tuple(box["center_xyz"]),
                size_lwh=tuple(box["size_lwh"]),
                yaw=float(box["yaw"]),
            )
            if parsed.class_name == "ball" and not np.isclose(parsed.yaw, 0.0):
                errors.append(f"{prefix}: ball yaw must be zero")
        except (KeyError, TypeError, ValueError) as error:
            errors.append(f"{prefix}: invalid box: {error}")
        attributes = box.get("attributes", {})
        if not isinstance(attributes, dict):
            errors.append(f"{prefix}: attributes must be an object")
            continue
        if attributes.get("difficulty") not in {"easy", "medium", "hard"}:
            errors.append(f"{prefix}: invalid difficulty")
        if not isinstance(attributes.get("num_points"), int) or attributes["num_points"] < 0:
            errors.append(f"{prefix}: num_points must be a non-negative integer")
        if (
            not isinstance(attributes.get("num_points_in_box"), int)
            or attributes["num_points_in_box"] < 0
        ):
            errors.append(f"{prefix}: num_points_in_box must be a non-negative integer")
        elif isinstance(attributes.get("num_points"), int) and (
            attributes["num_points"] > attributes["num_points_in_box"]
        ):
            errors.append(f"{prefix}: num_points cannot exceed num_points_in_box")
    return errors


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()
