from lidar_detection_ros.latest_slot import LatestValueSlot


def test_latest_value_replaces_stale_pending_work() -> None:
    slot: LatestValueSlot[int] = LatestValueSlot()

    assert slot.submit(1) is False
    assert slot.submit(2) is True
    assert slot.take(timeout=0.0) == 2
    assert slot.stats == (2, 1)


def test_close_releases_waiter_without_value() -> None:
    slot: LatestValueSlot[int] = LatestValueSlot()
    slot.close()
    assert slot.closed is True
    assert slot.take(timeout=0.0) is None
