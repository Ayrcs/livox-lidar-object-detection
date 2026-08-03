#!/usr/bin/env python3
import argparse
import hashlib
import shutil
from pathlib import Path


EXPECTED_CHECKPOINT_SHA256 = "33f2bc0f652f5a473b8c7d690bb2a578d7dc65231c3199a22f9373668e2a5944"


def main() -> None:
    parser = argparse.ArgumentParser(description="Package the validated pilot checkpoint")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    actual_digest = sha256_file(args.checkpoint)
    if actual_digest != EXPECTED_CHECKPOINT_SHA256:
        raise ValueError(f"unexpected checkpoint SHA-256: {actual_digest}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.checkpoint, args.output_dir / "model.pth")
    training_config = Path(
        "lidar_detection_training/configs/models/pointpillars_ball_pilot.py"
    ).read_text(encoding="utf-8")
    packaged_config = training_config.replace(
        "custom_imports = dict(imports=['lidar_training.mmdet3d_dataset'], allow_failed_imports=False)\n\n",
        "",
        1,
    )
    if packaged_config == training_config:
        raise ValueError("expected training-only custom_imports declaration was not found")
    (args.output_dir / "config.py").write_text(packaged_config, encoding="utf-8")
    shutil.copy2(args.run_dir / "environment.lock.txt", args.output_dir / "environment.lock.txt")
    shutil.copy2(args.run_dir / "nvidia-smi.txt", args.output_dir / "nvidia-smi.txt")
    shutil.copy2(args.run_dir / "git-commit.txt", args.output_dir / "git-commit.txt")

    checksum_path = args.output_dir / "SHA256SUMS"
    files = sorted(path for path in args.output_dir.iterdir() if path.is_file() and path != checksum_path)
    checksum_path.write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in files),
        encoding="utf-8",
    )
    print(args.output_dir)
    print(checksum_path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    main()
