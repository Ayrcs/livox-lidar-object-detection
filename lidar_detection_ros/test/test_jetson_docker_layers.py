from pathlib import Path


def test_application_dockerfile_does_not_rebuild_heavy_dependencies() -> None:
    repository_root = Path(__file__).parents[2]
    application = (repository_root / "docker" / "inference-jetson.Dockerfile").read_text(
        encoding="utf-8"
    )
    base = (
        repository_root / "docker" / "inference-jetson-base.Dockerfile"
    ).read_text(encoding="utf-8")

    dds_runtime = (
        repository_root / "docker" / "inference-jetson-dds.Dockerfile"
    ).read_text(encoding="utf-8")

    assert "ARG BASE_IMAGE=lidar-detection-jetson-runtime:0.2.0" in application
    assert "mim install mmcv" not in application
    assert "apt-get" not in application
    assert "/usr/local/lib/lidar_detection_ros/lidar_detection_node" in application
    assert "mim install mmcv==2.1.0" in base
    assert "COPY lidar_detection_ros" not in base
    assert "CYCLONEDDS_VERSION=0.10.2" in dds_runtime
    assert "c12abc56983204f1d91f2d839d394528c7b29b42" in dds_runtime
    assert "lidar-detection-jetson-base:0.1.0" in dds_runtime
    assert "mim install mmcv" not in dds_runtime


def test_unitree_cyclonedds_configuration_limits_multicast() -> None:
    repository_root = Path(__file__).parents[2]
    config = (repository_root / "docker" / "cyclonedds-unitree.xml").read_text(
        encoding="utf-8"
    )

    assert 'NetworkInterface name="eth0"' in config
    assert "<AllowMulticast>spdp</AllowMulticast>" in config
