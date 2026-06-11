#!/usr/bin/env python3
"""Subsystem heartbeat watchdog.

Each critical subsystem registers a maximum heartbeat interval. If a
subsystem fails to call heartbeat() within its timeout, check_all() reports
it so the fault manager can trigger RTB or E-Stop (design.md Watchdog spec).
"""

import threading
import time
from typing import Callable, Dict, List


class Watchdog:
    def __init__(self, time_fn: Callable[[], float] = time.monotonic):
        self._lock = threading.Lock()
        self._time_fn = time_fn
        self._timeouts: Dict[str, float] = {}
        self._last_heartbeat: Dict[str, float] = {}

    def register_subsystem(self, name: str, timeout_s: float) -> None:
        with self._lock:
            self._timeouts[name] = timeout_s
            self._last_heartbeat[name] = self._time_fn()

    def heartbeat(self, subsystem_name: str) -> None:
        with self._lock:
            if subsystem_name not in self._timeouts:
                raise KeyError(f"Unknown subsystem: {subsystem_name}")
            self._last_heartbeat[subsystem_name] = self._time_fn()

    def check_all(self) -> List[str]:
        """Returns the names of subsystems whose heartbeat has timed out."""
        now = self._time_fn()
        with self._lock:
            return [
                name
                for name, timeout in self._timeouts.items()
                if now - self._last_heartbeat[name] > timeout
            ]

    def is_healthy(self) -> bool:
        return len(self.check_all()) == 0
