"""Thread-safe latest-value slot for soft real-time perception."""

from __future__ import annotations

from threading import Condition
from typing import Generic, Optional, TypeVar


T = TypeVar("T")


class LatestValueSlot(Generic[T]):
    """Keep at most one pending item, replacing stale work on submission."""

    def __init__(self) -> None:
        self._condition = Condition()
        self._value: Optional[T] = None
        self._closed = False
        self._received = 0
        self._replaced = 0

    def submit(self, value: T) -> bool:
        """Store a value and return True when an older pending value was dropped."""

        with self._condition:
            if self._closed:
                return False
            replaced = self._value is not None
            if replaced:
                self._replaced += 1
            self._received += 1
            self._value = value
            self._condition.notify()
            return replaced

    def take(self, timeout: Optional[float] = None) -> Optional[T]:
        with self._condition:
            self._condition.wait_for(lambda: self._value is not None or self._closed, timeout)
            if self._value is None:
                return None
            value = self._value
            self._value = None
            return value

    def close(self) -> None:
        with self._condition:
            self._closed = True
            self._condition.notify_all()

    @property
    def stats(self) -> tuple[int, int]:
        with self._condition:
            return self._received, self._replaced

    @property
    def closed(self) -> bool:
        with self._condition:
            return self._closed
