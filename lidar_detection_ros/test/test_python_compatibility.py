import ast
from pathlib import Path


def test_runtime_sources_parse_as_python_3_8() -> None:
    package_root = Path(__file__).parents[1]
    for path in sorted(package_root.rglob("*.py")):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path), feature_version=(3, 8))


def test_packaged_config_has_no_training_dataset_import() -> None:
    repository_root = Path(__file__).parents[2]
    config = (
        repository_root
        / "model_registry"
        / "ball_pointpillars_pilot_v0.1.0"
        / "config.py"
    ).read_text(encoding="utf-8")
    assert "lidar_training.mmdet3d_dataset" not in config
