"""Standard ROS diagnostic output for the detector runtime."""

from __future__ import annotations

from typing import Any


def diagnostic_values(
    *,
    device: str,
    processing_ms: float,
    received_frames: int,
    dropped_frames: int,
    detection_count: int,
) -> dict[str, str]:
    return {
        "model_status": "ready",
        "device": device,
        "processing_ms": f"{processing_ms:.3f}",
        "received_frames": str(received_frames),
        "dropped_frames": str(dropped_frames),
        "detection_count": str(detection_count),
    }


def diagnostic_array_message(*, source_header: Any, values: dict[str, str]) -> Any:
    try:
        from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
    except ImportError as exc:  # pragma: no cover - requires ROS
        raise RuntimeError("diagnostic_msgs is required to publish runtime diagnostics") from exc

    output = DiagnosticArray()
    output.header.stamp = source_header.stamp
    status = DiagnosticStatus()
    status.name = "lidar_detection/runtime"
    status.hardware_id = values["device"]
    dropped = int(values["dropped_frames"])
    status.level = DiagnosticStatus.WARN if dropped else DiagnosticStatus.OK
    status.message = "running; stale frames replaced" if dropped else "running"
    status.values = [KeyValue(key=key, value=value) for key, value in values.items()]
    output.status.append(status)
    return output
