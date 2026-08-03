"""MMDetection3D registrations, imported only in the NVIDIA training environment."""

import numpy as np

try:
    from mmengine.evaluator import BaseMetric
    from mmdet3d.datasets import Det3DDataset
    from mmdet3d.registry import DATASETS, METRICS
    from mmdet3d.structures import LiDARInstance3DBoxes
except ModuleNotFoundError:
    # Allow config parsing and unit tests on the Mac preparation machine. The
    # Docker/NVIDIA environment must provide these imports before training.
    TRAINING_IMPORTS_AVAILABLE = False
else:
    TRAINING_IMPORTS_AVAILABLE = True


if TRAINING_IMPORTS_AVAILABLE:
    @DATASETS.register_module()
    class BallLidarDataset(Det3DDataset):
        METAINFO = {"classes": ("ball",), "palette": [(255, 80, 80)]}

        def parse_ann_info(self, info):
            ann_info = super().parse_ann_info(info)
            if ann_info is None:
                ann_info = {
                    "gt_bboxes_3d": np.zeros((0, 7), dtype=np.float32),
                    "gt_labels_3d": np.zeros(0, dtype=np.int64),
                }
            ann_info["gt_bboxes_3d"] = LiDARInstance3DBoxes(
                ann_info["gt_bboxes_3d"], box_dim=7, origin=(0.5, 0.5, 0.0)
            )
            return ann_info


    @METRICS.register_module()
    class BallCenterMetric(BaseMetric):
        """Pilot metric: greedy center matching at a configurable distance."""

        default_prefix = "ball"

        def __init__(self, match_distance_m=0.30, score_threshold=0.10, **kwargs):
            super().__init__(**kwargs)
            self.match_distance_m = float(match_distance_m)
            self.score_threshold = float(score_threshold)

        def process(self, data_batch, data_samples):
            for sample in data_samples:
                prediction = sample.pred_instances_3d
                ground_truth = sample.gt_instances_3d
                scores = prediction.scores_3d.detach().cpu().numpy()
                labels = prediction.labels_3d.detach().cpu().numpy()
                keep = (scores >= self.score_threshold) & (labels == 0)
                predicted_centers = prediction.bboxes_3d.center.detach().cpu().numpy()[keep]
                true_centers = ground_truth.bboxes_3d.center.detach().cpu().numpy()
                self.results.append(
                    _match_centers(predicted_centers, true_centers, self.match_distance_m)
                )

        def compute_metrics(self, results):
            true_positive = sum(result["true_positive"] for result in results)
            false_positive = sum(result["false_positive"] for result in results)
            false_negative = sum(result["false_negative"] for result in results)
            distances = [distance for result in results for distance in result["distances"]]
            precision = true_positive / max(true_positive + false_positive, 1)
            recall = true_positive / max(true_positive + false_negative, 1)
            return {
                "precision_center_0p30m": precision,
                "recall_center_0p30m": recall,
                "f1_center_0p30m": 2 * precision * recall / max(precision + recall, 1e-12),
                "median_center_error_m": (
                    float(np.median(distances)) if distances else float("nan")
                ),
                "false_positives_per_sample": false_positive / max(len(results), 1),
            }


def _match_centers(predicted, expected, threshold):
    candidates = []
    for prediction_index, prediction in enumerate(predicted):
        for expected_index, target in enumerate(expected):
            candidates.append((float(np.linalg.norm(prediction - target)), prediction_index, expected_index))
    matched_predictions = set()
    matched_expected = set()
    distances = []
    for distance, prediction_index, expected_index in sorted(candidates):
        if distance > threshold:
            break
        if prediction_index in matched_predictions or expected_index in matched_expected:
            continue
        matched_predictions.add(prediction_index)
        matched_expected.add(expected_index)
        distances.append(distance)
    return {
        "true_positive": len(distances),
        "false_positive": len(predicted) - len(distances),
        "false_negative": len(expected) - len(distances),
        "distances": distances,
    }
