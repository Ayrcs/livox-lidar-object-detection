"""Resolve and integrity-check a packaged detector model."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Optional, Union


@dataclass(frozen=True)
class ModelPackage:
    root: Path
    checkpoint_path: Path
    config_path: Path


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sha256sums(root: Path) -> None:
    sums_path = root / "SHA256SUMS"
    if not sums_path.is_file():
        raise ValueError(f"model package is missing {sums_path.name}")
    entries = 0
    for line_number, raw_line in enumerate(sums_path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64:
            raise ValueError(f"invalid SHA256SUMS line {line_number}")
        expected, relative_name = parts
        relative_name = relative_name.lstrip("*")
        relative_path = Path(relative_name)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"unsafe SHA256SUMS path: {relative_name}")
        artifact = root / relative_path
        if not artifact.is_file():
            raise ValueError(f"model package is missing {relative_name}")
        actual = _sha256_file(artifact)
        if actual != expected.lower():
            raise ValueError(
                f"SHA-256 mismatch for {relative_name}: expected {expected.lower()}, got {actual}"
            )
        entries += 1
    if entries == 0:
        raise ValueError("SHA256SUMS contains no artifacts")


def resolve_model_package(
    model_path: Union[str, Path],
    *,
    config_path: Optional[Union[str, Path]] = None,
) -> ModelPackage:
    path = Path(model_path)
    if path.is_dir():
        verify_sha256sums(path)
        checkpoint = path / "model.pth"
        config = path / "config.py"
        root = path
    elif path.is_file():
        if not config_path:
            raise ValueError("config_path is required when model_path points directly to a file")
        checkpoint = path
        config = Path(config_path)
        root = path.parent
    else:
        raise ValueError(f"model_path does not exist: {path}")

    if not checkpoint.is_file():
        raise ValueError(f"model checkpoint does not exist: {checkpoint}")
    if not config.is_file():
        raise ValueError(f"model config does not exist: {config}")
    return ModelPackage(root=root, checkpoint_path=checkpoint, config_path=config)
