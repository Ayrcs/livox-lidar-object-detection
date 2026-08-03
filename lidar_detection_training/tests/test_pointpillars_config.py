from pathlib import Path

import pytest


mmengine = pytest.importorskip("mmengine")
from mmengine.config import Config


@pytest.mark.parametrize(
    "relative_path",
    [
        "configs/models/pointpillars_ball_pilot.py",
        "configs/experiments/pointpillars_ball_overfit_v1.py",
    ],
)
def test_single_class_anchor_configuration(relative_path: str) -> None:
    package_root = Path(__file__).parents[1]
    config = Config.fromfile(package_root / relative_path)
    head = config.model.bbox_head
    assert head.num_classes == 1
    assert head.assign_per_class is False
    assert head.anchor_generator.reshape_out is True
    assert head.use_direction_classifier is True
    assert head.loss_dir.loss_weight == 0.0
    assert isinstance(config.model.train_cfg.assigner, dict)
    assert config.randomness.seed == 20260803
    assert config.randomness.deterministic is False
