from lidar_detection_ros.diagnostics import diagnostic_values


def test_diagnostic_values_are_stable_strings() -> None:
    values = diagnostic_values(
        device="cuda:0",
        processing_ms=12.34567,
        received_frames=101,
        dropped_frames=4,
        detection_count=1,
    )

    assert values == {
        "model_status": "ready",
        "device": "cuda:0",
        "processing_ms": "12.346",
        "received_frames": "101",
        "dropped_frames": "4",
        "detection_count": "1",
    }
