from types import SimpleNamespace

import numpy as np

from lidar_training.rosbag_io import pointcloud2_to_numpy


def test_decode_and_roll_correction() -> None:
    dtype = np.dtype({
        "names": ["x", "y", "z", "intensity", "ring", "time"],
        "formats": ["<f4", "<f4", "<f4", "<f4", "<u2", "<f4"],
        "offsets": [0, 4, 8, 12, 16, 18],
        "itemsize": 22,
    })
    data = np.zeros(1, dtype=dtype)
    data[0] = (1.0, 2.0, -3.0, 42.0, 7, 0.01)
    fields = [
        SimpleNamespace(name=name, offset=offset, datatype=datatype)
        for name, (offset, datatype) in {
            "x": (0, 7), "y": (4, 7), "z": (8, 7), "intensity": (12, 7), "ring": (16, 4), "time": (18, 7)
        }.items()
    ]
    message = SimpleNamespace(is_bigendian=False, height=1, width=1, point_step=22, fields=fields, data=data.tobytes())
    points = pointcloud2_to_numpy(message)
    np.testing.assert_allclose(points[0], [1.0, -2.0, 3.0, 42.0, 7.0, 0.01])
