from types import SimpleNamespace

import numpy as np
import pytest

from lidar_detection_ros.pointcloud_adapter import pointcloud2_to_model_array


def _message(points: np.ndarray) -> SimpleNamespace:
    dtype = np.dtype(
        {
            "names": ["x", "y", "z", "intensity", "ring", "time"],
            "formats": ["<f4", "<f4", "<f4", "<f4", "<u2", "<f4"],
            "offsets": [0, 4, 8, 12, 16, 18],
            "itemsize": 22,
        }
    )
    records = np.zeros(len(points), dtype=dtype)
    for index, name in enumerate(("x", "y", "z", "intensity")):
        records[name] = points[:, index]
    fields = [
        SimpleNamespace(name=name, offset=offset, datatype=7)
        for name, offset in zip(("x", "y", "z", "intensity"), (0, 4, 8, 12), strict=True)
    ]
    fields += [
        SimpleNamespace(name="ring", offset=16, datatype=4),
        SimpleNamespace(name="time", offset=18, datatype=7),
    ]
    return SimpleNamespace(
        is_bigendian=False,
        height=1,
        width=len(points),
        point_step=22,
        fields=fields,
        data=records.tobytes(),
    )


def test_decodes_livox_layout_and_corrects_mounting() -> None:
    raw = np.array([[1.0, -2.0, -3.0, 4.0], [5.0, 6.0, 7.0, 8.0]], dtype=np.float32)
    actual = pointcloud2_to_model_array(_message(raw))
    expected = raw.copy()
    expected[:, 1:3] *= -1
    np.testing.assert_array_equal(actual, expected)
    assert actual.flags.c_contiguous


def test_rejects_missing_intensity() -> None:
    message = _message(np.ones((1, 4), dtype=np.float32))
    message.fields = [field for field in message.fields if field.name != "intensity"]
    with pytest.raises(ValueError, match="missing model fields"):
        pointcloud2_to_model_array(message)
