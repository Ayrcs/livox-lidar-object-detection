import json
from pathlib import Path

import numpy as np

from .types import Box3D, Sample


def load_sample(npz_path: Path, annotation_path: Path | None = None) -> Sample:
    """Load canonical points plus a sidecar JSON annotation.

    The NPZ must contain points, sample_id, session_id, timestamp_ns and frame_id.
    """
    with np.load(npz_path, allow_pickle=False) as data:
        points = np.asarray(data["points"])
        metadata = {key: data[key].item() for key in ("sample_id", "session_id", "timestamp_ns", "frame_id")}
    boxes: tuple[Box3D, ...] = ()
    sidecar = annotation_path or npz_path.with_suffix(".json")
    if sidecar.exists():
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        boxes = tuple(Box3D(**item) for item in payload.get("boxes", []))
    return Sample(points=points, boxes=boxes, **metadata)
