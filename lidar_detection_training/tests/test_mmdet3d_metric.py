import numpy as np

from lidar_training.mmdet3d_dataset import _field, _match_centers


class Container:
    value = 7


def test_field_supports_dict_and_attribute_containers() -> None:
    assert _field({"value": 3}, "value") == 3
    assert _field(Container(), "value") == 7


def test_match_centers_is_one_to_one() -> None:
    result = _match_centers(
        np.asarray([[1.02, 0.0, 0.0], [1.08, 0.0, 0.0], [3.0, 0.0, 0.0]]),
        np.asarray([[1.0, 0.0, 0.0]]),
        threshold=0.30,
    )
    assert result["true_positive"] == 1
    assert result["false_positive"] == 2
    assert result["false_negative"] == 0
    assert result["distances"] == [0.020000000000000018]
