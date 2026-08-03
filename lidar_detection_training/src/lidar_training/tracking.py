from dataclasses import dataclass

import numpy as np

from .types import Box3D


@dataclass(frozen=True)
class TrackerConfig:
    association_distance_m: float = 0.35
    confirmation_hits: int = 2
    max_misses: int = 2
    alpha: float = 0.85
    beta: float = 0.10


class BallTracker:
    """Single-target deterministic alpha-beta tracker for the pilot baseline."""

    def __init__(self, config: TrackerConfig = TrackerConfig()) -> None:
        self.config = config
        self._position: np.ndarray | None = None
        self._velocity = np.zeros(3, dtype=np.float64)
        self._last_timestamp_ns: int | None = None
        self._hits = 0
        self._misses = 0

    def update(self, detections: list[Box3D], timestamp_ns: int) -> Box3D | None:
        if self._position is None:
            if not detections:
                return None
            seed = max(detections, key=_point_count)
            self._position = np.asarray(seed.center_xyz, dtype=np.float64)
            self._last_timestamp_ns = timestamp_ns
            self._hits = 1
            self._misses = 0
            return self._output(seed, predicted=False) if self._confirmed else None

        dt = max((timestamp_ns - int(self._last_timestamp_ns)) / 1_000_000_000, 1e-6)
        predicted_position = self._position + self._velocity * dt
        match = _nearest_detection(detections, predicted_position, self.config.association_distance_m)
        self._last_timestamp_ns = timestamp_ns
        if match is not None:
            observed = np.asarray(match.center_xyz, dtype=np.float64)
            residual = observed - predicted_position
            self._position = predicted_position + self.config.alpha * residual
            self._velocity = self._velocity + (self.config.beta / dt) * residual
            self._hits += 1
            self._misses = 0
            return self._output(match, predicted=False) if self._confirmed else None

        self._position = predicted_position
        self._misses += 1
        if self._misses > self.config.max_misses:
            self.reset()
            return None
        if not self._confirmed:
            return None
        return self._output(None, predicted=True)

    def reset(self) -> None:
        self._position = None
        self._velocity = np.zeros(3, dtype=np.float64)
        self._last_timestamp_ns = None
        self._hits = 0
        self._misses = 0

    @property
    def _confirmed(self) -> bool:
        return self._hits >= self.config.confirmation_hits

    def _output(self, source: Box3D | None, predicted: bool) -> Box3D:
        attributes = dict(source.attributes) if source is not None else {}
        attributes.update(
            {
                "source": "geometric_baseline_tracker",
                "track_hits": self._hits,
                "track_misses": self._misses,
                "predicted": predicted,
            }
        )
        return Box3D(
            "ball",
            tuple(float(value) for value in self._position),
            (0.22, 0.22, 0.22),
            0.0,
            attributes,
        )


def _point_count(detection: Box3D) -> int:
    return int(detection.attributes.get("num_points", 0))


def _nearest_detection(
    detections: list[Box3D], predicted_position: np.ndarray, max_distance_m: float
) -> Box3D | None:
    eligible = [
        (float(np.linalg.norm(np.asarray(item.center_xyz) - predicted_position)), -_point_count(item), item)
        for item in detections
    ]
    eligible = [entry for entry in eligible if entry[0] <= max_distance_m]
    return min(eligible, key=lambda entry: (entry[0], entry[1]))[2] if eligible else None
