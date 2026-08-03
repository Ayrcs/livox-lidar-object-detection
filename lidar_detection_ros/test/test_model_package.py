from hashlib import sha256
from pathlib import Path

import pytest

from lidar_detection_ros.model_package import resolve_model_package


def _write_package(root: Path) -> None:
    artifacts = {"model.pth": b"checkpoint", "config.py": b"model = {}\n"}
    sums = []
    for name, content in artifacts.items():
        (root / name).write_bytes(content)
        sums.append(f"{sha256(content).hexdigest()}  {name}")
    (root / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")


def test_resolves_and_verifies_model_directory(tmp_path: Path) -> None:
    _write_package(tmp_path)
    package = resolve_model_package(tmp_path)
    assert package.checkpoint_path == tmp_path / "model.pth"
    assert package.config_path == tmp_path / "config.py"


def test_rejects_corrupted_artifact(tmp_path: Path) -> None:
    _write_package(tmp_path)
    (tmp_path / "model.pth").write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        resolve_model_package(tmp_path)


def test_direct_checkpoint_requires_explicit_config(tmp_path: Path) -> None:
    checkpoint = tmp_path / "model.pth"
    checkpoint.write_bytes(b"checkpoint")
    with pytest.raises(ValueError, match="config_path is required"):
        resolve_model_package(checkpoint)
