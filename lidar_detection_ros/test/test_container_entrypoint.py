from pathlib import Path


def test_entrypoint_exposes_pip_ament_prefix() -> None:
    repository_root = Path(__file__).parents[2]
    entrypoint = (repository_root / "docker" / "ros_entrypoint.sh").read_text(
        encoding="utf-8"
    )
    assert 'source /opt/ros/foxy/setup.bash' in entrypoint
    assert 'export AMENT_PREFIX_PATH="/usr/local:${AMENT_PREFIX_PATH}"' in entrypoint
    assert 'exec "$@"' in entrypoint
