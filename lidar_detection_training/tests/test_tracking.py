from lidar_training.tracking import BallTracker, TrackerConfig
from lidar_training.types import Box3D


def detection(x: float, points: int = 5) -> Box3D:
    return Box3D("ball", (x, 0.0, 0.11), (0.22, 0.22, 0.22), attributes={"num_points": points})


def test_tracker_confirms_and_coasts() -> None:
    tracker = BallTracker(TrackerConfig(confirmation_hits=2, max_misses=2))
    assert tracker.update([detection(1.0)], 0) is None
    confirmed = tracker.update([detection(1.01)], 100_000_000)
    assert confirmed is not None
    assert confirmed.attributes["predicted"] is False
    coasted = tracker.update([], 200_000_000)
    assert coasted is not None
    assert coasted.attributes["predicted"] is True
    assert tracker.update([], 300_000_000) is not None
    assert tracker.update([], 400_000_000) is None


def test_isolated_candidate_never_confirms() -> None:
    tracker = BallTracker(TrackerConfig(confirmation_hits=2, max_misses=1))
    assert tracker.update([detection(1.0)], 0) is None
    assert tracker.update([], 100_000_000) is None
    assert tracker.update([], 200_000_000) is None
