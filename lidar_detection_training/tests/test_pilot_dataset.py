import pytest

from lidar_training.pilot_dataset import annotation_to_mmdet_instance, evenly_spaced


def test_evenly_spaced_keeps_endpoints() -> None:
    items = [{"value": value} for value in range(10)]
    assert [item["value"] for item in evenly_spaced(items, 3)] == [0, 4, 9]
    assert evenly_spaced(items, 0) == []
    with pytest.raises(ValueError):
        evenly_spaced(items, -1)


def test_annotation_converts_center_z_to_mmdet_bottom_z() -> None:
    box = {
        "center_xyz": [3.0, 0.2, -1.0],
        "size_lwh": [0.22, 0.22, 0.22],
        "yaw": 0.0,
        "attributes": {"num_points": 8},
    }
    instance = annotation_to_mmdet_instance(box)
    assert instance["bbox_3d"] == pytest.approx([3.0, 0.2, -1.11, 0.22, 0.22, 0.22, 0.0])
    assert instance["bbox_label_3d"] == 0
    assert instance["num_lidar_pts"] == 8
