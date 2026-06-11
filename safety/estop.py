#!/usr/bin/env python3
"""Software emergency stop.

The E-Stop is the highest-priority safety primitive. Once triggered, the
core control loop must halt all locomotion and manipulator commands until
an authorized reset clears it (design.md Correctness Property P5). It can
be triggered by any subsystem: fault manager, watchdog, geofence, vision,
or a remote command.
"""

import threading
import time
from typing import Optional


class EStop:
    def __init__(self, reset_token: Optional[str] = None):
        """`reset_token`, if set, must be supplied to `reset()` to clear a
        trigger. Leave as None for units where reset authorization is
        enforced upstream (e.g. the connectivity layer validates a signed
        remote command before calling reset())."""
        self._lock = threading.Lock()
        self._armed = False
        self._triggered = False
        self._reason: Optional[str] = None
        self._source: Optional[str] = None
        self._triggered_at: Optional[float] = None
        self._reset_token = reset_token

    def arm(self) -> None:
        with self._lock:
            self._armed = True

    def trigger(self, reason: str, source: str) -> None:
        with self._lock:
            self._triggered = True
            self._reason = reason
            self._source = source
            self._triggered_at = time.time()

    def reset(self, auth_token: Optional[str] = None) -> bool:
        """Clear a trigger. Returns False (and leaves the trigger active)
        if a reset token is configured and `auth_token` doesn't match."""
        with self._lock:
            if not self._triggered:
                return True
            if self._reset_token is not None and auth_token != self._reset_token:
                return False
            self._triggered = False
            self._reason = None
            self._source = None
            self._triggered_at = None
            return True

    def is_armed(self) -> bool:
        with self._lock:
            return self._armed

    def is_triggered(self) -> bool:
        with self._lock:
            return self._triggered

    def get_trigger_reason(self) -> Optional[str]:
        with self._lock:
            return self._reason

    def get_trigger_source(self) -> Optional[str]:
        with self._lock:
            return self._source

    def get_trigger_time(self) -> Optional[float]:
        with self._lock:
            return self._triggered_at
