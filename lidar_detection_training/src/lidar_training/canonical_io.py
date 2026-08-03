import hashlib
import json
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from .types import Sample


CANONICAL_FIELDS = ["x", "y", "z", "intensity", "ring", "time"]
SCHEMA_VERSION = 1


def write_canonical_sample(
    output_root: Path,
    sample_id: str,
    points: NDArray[np.floating],
    metadata: dict[str, object],
) -> dict[str, object]:
    """Write deterministic NPY + JSON files and return their manifest entry."""
    if points.ndim != 2 or points.shape[1] != len(CANONICAL_FIELDS):
        raise ValueError(f"points must have shape (N, {len(CANONICAL_FIELDS)})")
    if points.dtype != np.float32:
        raise ValueError("canonical points must use float32")
    if not sample_id or any(character in sample_id for character in "/\\"):
        raise ValueError("sample_id must be a non-empty filename-safe identifier")

    points_dir = output_root / "points"
    metadata_dir = output_root / "metadata"
    points_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    points_path = points_dir / f"{sample_id}.npy"
    metadata_path = metadata_dir / f"{sample_id}.json"

    canonical_points = np.ascontiguousarray(points, dtype="<f4")
    with points_path.open("wb") as stream:
        np.lib.format.write_array(stream, canonical_points, allow_pickle=False)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "sample_id": sample_id,
        "point_fields": CANONICAL_FIELDS,
        "point_dtype": "float32_little_endian",
        "point_count": len(points),
        **metadata,
    }
    metadata_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "sample_id": sample_id,
        "points_path": points_path.relative_to(output_root).as_posix(),
        "metadata_path": metadata_path.relative_to(output_root).as_posix(),
        "points_sha256": sha256_file(points_path),
        "metadata_sha256": sha256_file(metadata_path),
        "point_count": len(points),
    }


def load_canonical_sample(output_root: Path, sample_id: str) -> Sample:
    metadata_path = output_root / "metadata" / f"{sample_id}.json"
    points_path = output_root / "points" / f"{sample_id}.npy"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    points = np.load(points_path, allow_pickle=False)
    if metadata["point_fields"] != CANONICAL_FIELDS:
        raise ValueError("canonical point fields do not match this reader")
    return Sample(
        sample_id=sample_id,
        session_id=metadata["session_id"],
        timestamp_ns=metadata["header_timestamp_ns"],
        frame_id=metadata["frame_id"],
        points=points,
    )


def write_dataset_manifest(output_root: Path, entries: list[dict[str, object]], metadata: dict[str, object]) -> Path:
    manifest_path = output_root / "dataset_manifest.json"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "sample_count": len(entries),
        "samples": sorted(entries, key=lambda entry: str(entry["sample_id"])),
        **metadata,
    }
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
