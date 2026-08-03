"""Efficient ROS PointCloud2 to model-array conversion."""

from __future__ import annotations

from typing import Any

import numpy as np


FLOAT32 = 7
MODEL_FIELDS = ("x", "y", "z", "intensity")


def pointcloud2_to_model_array(message: Any, *, correct_upside_down: bool = True) -> np.ndarray:
    """Decode x/y/z/intensity without creating one Python object per point."""

    if bool(message.is_bigendian):
        raise ValueError("big-endian PointCloud2 is not supported")
    if int(message.height) != 1:
        raise ValueError(f"only unorganized PointCloud2 is supported, received height={message.height}")

    fields = {field.name: field for field in message.fields}
    missing = [name for name in MODEL_FIELDS if name not in fields]
    if missing:
        raise ValueError(f"PointCloud2 is missing model fields: {', '.join(missing)}")
    invalid = [name for name in MODEL_FIELDS if int(fields[name].datatype) != FLOAT32]
    if invalid:
        raise ValueError(f"model fields must be FLOAT32: {', '.join(invalid)}")

    point_step = int(message.point_step)
    offsets = [int(fields[name].offset) for name in MODEL_FIELDS]
    if any(offset < 0 or offset + 4 > point_step for offset in offsets):
        raise ValueError(f"field offset exceeds point_step={point_step}")

    dtype = np.dtype(
        {
            "names": list(MODEL_FIELDS),
            "formats": ["<f4"] * len(MODEL_FIELDS),
            "offsets": offsets,
            "itemsize": point_step,
        }
    )
    count = int(message.width)
    expected_bytes = count * point_step
    if len(message.data) < expected_bytes:
        raise ValueError(
            f"PointCloud2 data is truncated: expected {expected_bytes} bytes, got {len(message.data)}"
        )

    records = np.frombuffer(message.data, dtype=dtype, count=count)
    points = np.empty((count, 4), dtype=np.float32)
    for index, name in enumerate(MODEL_FIELDS):
        points[:, index] = records[name]

    points = points[np.isfinite(points).all(axis=1)]
    if correct_upside_down:
        points[:, 1:3] *= -1.0
    return np.ascontiguousarray(points)
