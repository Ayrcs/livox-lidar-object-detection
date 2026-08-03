from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray


EXPECTED_FIELDS = {
    "x": (0, 7),          # sensor_msgs/PointField.FLOAT32
    "y": (4, 7),
    "z": (8, 7),
    "intensity": (12, 7),
    "ring": (16, 4),      # sensor_msgs/PointField.UINT16
    "time": (18, 7),
}


@dataclass(frozen=True)
class PointCloudFrame:
    message_index: int
    bag_timestamp_ns: int
    header_timestamp_ns: int
    frame_id: str
    points: NDArray[np.float32]


def pointcloud2_to_numpy(message: object, correct_upside_down: bool = True) -> NDArray[np.float32]:
    """Decode the measured Unitree 22-byte PointCloud2 layout.

    Columns are x, y, z, intensity, ring and relative time. When requested, the
    verified 180-degree roll correction maps raw (x, y, z) to (x, -y, -z).
    """
    if bool(message.is_bigendian):
        raise ValueError("big-endian PointCloud2 is not supported")
    if int(message.height) != 1:
        raise ValueError(f"expected height=1, got {message.height}")
    if int(message.point_step) != 22:
        raise ValueError(f"expected point_step=22, got {message.point_step}")
    actual = {field.name: (field.offset, field.datatype) for field in message.fields}
    if actual != EXPECTED_FIELDS:
        raise ValueError(f"unexpected fields: {actual}")

    dtype = np.dtype(
        {
            "names": ["x", "y", "z", "intensity", "ring", "time"],
            "formats": ["<f4", "<f4", "<f4", "<f4", "<u2", "<f4"],
            "offsets": [0, 4, 8, 12, 16, 18],
            "itemsize": 22,
        }
    )
    count = int(message.width) * int(message.height)
    records = np.frombuffer(message.data, dtype=dtype, count=count)
    points = np.empty((count, 6), dtype=np.float32)
    for column, name in enumerate(("x", "y", "z", "intensity", "ring", "time")):
        points[:, column] = records[name]
    if correct_upside_down:
        points[:, 1:3] *= -1.0
    return points


def iter_pointcloud_frames(bag_dir: Path) -> Iterator[PointCloudFrame]:
    """Yield decoded PointCloud2 frames from a ROS 2 Foxy rosbag directory."""
    try:
        from rosbags.highlevel import AnyReader
        from rosbags.typesys import Stores, get_typestore
    except ImportError as error:
        raise RuntimeError("Install the project with the 'rosbag' extra") from error

    with AnyReader(
        [bag_dir], default_typestore=get_typestore(Stores.ROS2_FOXY)
    ) as reader:
        connections = [
            connection
            for connection in reader.connections
            if connection.topic == "/utlidar/cloud_livox_mid360"
        ]
        if len(connections) != 1:
            raise ValueError(f"expected one LiDAR connection, found {len(connections)}")
        for message_index, (connection, timestamp, rawdata) in enumerate(
            reader.messages(connections=connections)
        ):
            message = reader.deserialize(rawdata, connection.msgtype)
            header_timestamp = int(message.header.stamp.sec) * 1_000_000_000 + int(
                message.header.stamp.nanosec
            )
            yield PointCloudFrame(
                message_index=message_index,
                bag_timestamp_ns=timestamp,
                header_timestamp_ns=header_timestamp,
                frame_id=message.header.frame_id,
                points=pointcloud2_to_numpy(message),
            )
