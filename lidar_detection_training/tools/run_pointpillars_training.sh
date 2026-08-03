#!/usr/bin/env bash
set -euo pipefail

# Required by PyTorch deterministic algorithms for cuBLAS on CUDA >= 10.2.
export CUBLAS_WORKSPACE_CONFIG=:4096:8

mode="${1:-overfit}"
case "$mode" in
  overfit)
    config="lidar_detection_training/configs/experiments/pointpillars_ball_overfit_v1.py"
    work_dir="runs/pointpillars_ball_overfit_v1"
    ;;
  pilot)
    config="lidar_detection_training/configs/models/pointpillars_ball_pilot.py"
    work_dir="runs/pointpillars_ball_pilot_v1"
    ;;
  *)
    echo "Usage: $0 [overfit|pilot]" >&2
    exit 2
    ;;
esac

test -f "$config"
test -f data/processed/ball_lidar_pilot_v1_mmdet3d/pilot_dataset_manifest.json
command -v nvidia-smi >/dev/null
nvidia-smi >/dev/null

mkdir -p "$work_dir"
nvidia-smi > "$work_dir/nvidia-smi.txt"
python --version > "$work_dir/python-version.txt" 2>&1
python -m pip freeze > "$work_dir/environment.lock.txt"
git rev-parse HEAD > "$work_dir/git-commit.txt"

python - <<'PY'
import torch
import mmcv
import mmdet
import mmdet3d
import mmengine

assert torch.cuda.is_available(), "CUDA is not available to PyTorch"
print("torch", torch.__version__, "cuda", torch.version.cuda)
print("mmengine", mmengine.__version__)
print("mmcv", mmcv.__version__)
print("mmdet", mmdet.__version__)
print("mmdet3d", mmdet3d.__version__)
print("gpu", torch.cuda.get_device_name(0))
PY

python /opt/mmdetection3d/tools/train.py "$config" --work-dir "$work_dir"
