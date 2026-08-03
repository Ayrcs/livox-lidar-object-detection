from pathlib import Path


def test_application_dockerfile_does_not_rebuild_heavy_dependencies() -> None:
    repository_root = Path(__file__).parents[2]
    application = (repository_root / "docker" / "inference-jetson.Dockerfile").read_text(
        encoding="utf-8"
    )
    base = (
        repository_root / "docker" / "inference-jetson-base.Dockerfile"
    ).read_text(encoding="utf-8")

    assert "ARG BASE_IMAGE=lidar-detection-jetson-base:0.1.0" in application
    assert "mim install mmcv" not in application
    assert "apt-get" not in application
    assert "/usr/local/lib/lidar_detection_ros/lidar_detection_node" in application
    assert "mim install mmcv==2.1.0" in base
    assert "COPY lidar_detection_ros" not in base
