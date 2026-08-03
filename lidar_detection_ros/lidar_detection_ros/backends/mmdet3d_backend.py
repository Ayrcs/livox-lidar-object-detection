"""MMDetection3D PointPillars inference adapter."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from lidar_detection_ros.types import Detection3D


def ensure_jetson_torch_distributed_compatibility(torch_module: Any = None) -> bool:
    """Provide the API surface MMEngine imports on NVIDIA's Jetson PyTorch.

    Some Jetson PyTorch wheels expose ``torch.distributed`` without
    ``ReduceOp``. MMEngine evaluates that symbol while importing, even for
    single-process inference. The placeholder only lets that import complete;
    it does not add distributed-training support.

    Returns ``True`` when the compatibility placeholder was installed.
    """

    if torch_module is None:  # pragma: no cover - exercised in Jetson container
        import torch as torch_module

    distributed = getattr(torch_module, "distributed", None)
    if distributed is None or hasattr(distributed, "ReduceOp"):
        return False

    class ReduceOp:
        SUM = "sum"
        PRODUCT = "product"
        MIN = "min"
        MAX = "max"
        BAND = "band"
        BOR = "bor"
        BXOR = "bxor"
        AVG = "avg"
        PREMUL_SUM = "premul_sum"

    distributed.ReduceOp = ReduceOp
    return True


def prepare_inference_config(config: Any) -> Any:
    """Replace the training-only dataset used by ``init_model`` metadata lookup.

    MMDetection3D builds ``test_dataloader.dataset`` only to obtain its
    metainfo when an older checkpoint does not embed it. Runtime inference has
    neither annotations nor a need for the custom training dataset, so a lazy
    built-in dataset supplies the packaged ``metainfo`` without reading data.
    """

    dataset = config["test_dataloader"]["dataset"]
    dataset["type"] = "Det3DDataset"
    dataset["lazy_init"] = True
    return config


def _to_numpy(value: Any) -> np.ndarray:
    """Convert a Torch-like tensor or an array to a CPU NumPy array."""

    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        value = value.numpy()
    return np.asarray(value)


def _field(container: Any, name: str) -> Any:
    if isinstance(container, dict):
        return container[name]
    return getattr(container, name)


def detections_from_result(
    result: Any,
    *,
    class_names: Sequence[str],
    score_threshold: float,
    fixed_box_sizes: dict[str, tuple[float, float, float]] | None = None,
) -> list[Detection3D]:
    """Normalize an MMDetection3D result into stable Python values."""

    if isinstance(result, tuple):
        result = result[0]
    if isinstance(result, list):
        if len(result) != 1:
            raise ValueError(f"Expected one inference result, received {len(result)}")
        result = result[0]

    instances = _field(result, "pred_instances_3d")
    boxes = _field(instances, "bboxes_3d")
    boxes = _to_numpy(boxes.tensor if hasattr(boxes, "tensor") else boxes)
    scores = _to_numpy(_field(instances, "scores_3d")).reshape(-1)
    labels = _to_numpy(_field(instances, "labels_3d")).astype(np.int64).reshape(-1)

    if boxes.ndim != 2 or boxes.shape[1] < 7:
        raise ValueError(f"Expected boxes with shape (N, >=7), received {boxes.shape}")
    if not (len(boxes) == len(scores) == len(labels)):
        raise ValueError("MMDetection3D returned inconsistent box, score and label counts")

    fixed_box_sizes = fixed_box_sizes or {}
    detections: list[Detection3D] = []
    for box, score, label in zip(boxes, scores, labels):
        if float(score) < score_threshold:
            continue
        if label < 0 or label >= len(class_names):
            raise ValueError(f"Unknown class id returned by model: {label}")

        class_name = class_names[int(label)]
        length, width, height = (float(v) for v in box[3:6])
        yaw = float(box[6])
        if class_name in fixed_box_sizes:
            length, width, height = fixed_box_sizes[class_name]
            if class_name == "ball":
                yaw = 0.0

        detections.append(
            Detection3D(
                class_id=int(label),
                class_name=class_name,
                score=float(score),
                x=float(box[0]),
                y=float(box[1]),
                z=float(box[2]),
                length=length,
                width=width,
                height=height,
                yaw=yaw,
            )
        )
    return detections


class MMDetection3DBackend:
    """Load one MMDetection3D checkpoint and infer on NumPy point clouds."""

    def __init__(
        self,
        *,
        config_path: str | Path,
        checkpoint_path: str | Path,
        device: str = "cuda:0",
        class_names: Sequence[str] = ("ball",),
        score_threshold: float = 0.10,
        fixed_box_sizes: dict[str, tuple[float, float, float]] | None = None,
    ) -> None:
        ensure_jetson_torch_distributed_compatibility()
        try:
            from mmengine import Config
            from mmdet3d.apis import init_model
        except ImportError as exc:  # pragma: no cover - exercised in GPU container
            raise RuntimeError(
                "MMDetection3D is required for this backend; use the project inference/training container"
            ) from exc

        self._inference_detector = self._load_inference_function()
        runtime_config = prepare_inference_config(Config.fromfile(str(config_path)))
        self._model = init_model(runtime_config, str(checkpoint_path), device=device)
        self._class_names = tuple(class_names)
        self._score_threshold = score_threshold
        self._fixed_box_sizes = fixed_box_sizes

    @staticmethod
    def _load_inference_function():
        from mmdet3d.apis import inference_detector

        return inference_detector

    def predict(self, points: np.ndarray) -> list[Detection3D]:
        cloud = np.asarray(points, dtype=np.float32)
        if cloud.ndim != 2 or cloud.shape[1] != 4:
            raise ValueError(f"Expected float point cloud with shape (N, 4), received {cloud.shape}")
        if not np.isfinite(cloud).all():
            raise ValueError("Point cloud contains NaN or infinite values")

        result = self._inference_detector(self._model, cloud)
        return detections_from_result(
            result,
            class_names=self._class_names,
            score_threshold=self._score_threshold,
            fixed_box_sizes=self._fixed_box_sizes,
        )
