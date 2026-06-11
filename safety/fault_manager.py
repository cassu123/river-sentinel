#!/usr/bin/env python3
"""Central fault registry.

Subsystems report faults here. Severity-specific handlers - registered by
core/orchestrator.py during boot - decide the response: log, alert, RTB,
or E-Stop. FaultManager itself has no knowledge of locomotion or
connectivity; it only tracks fault state and dispatches to registered
handlers (design.md FaultManager spec).
"""

import threading
import time
from typing import Callable, Dict, List

from core.models import Fault, FaultSeverity

_SEVERITY_ORDER = [
    FaultSeverity.INFO,
    FaultSeverity.WARNING,
    FaultSeverity.CRITICAL,
    FaultSeverity.FATAL,
]


class FaultManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._active_faults: Dict[str, Fault] = {}
        self._handlers: Dict[FaultSeverity, Callable[[Fault], None]] = {}

    def register_handler(self, severity: FaultSeverity, handler: Callable[[Fault], None]) -> None:
        with self._lock:
            self._handlers[severity] = handler

    def report_fault(self, fault: Fault) -> None:
        """Registers `fault` (keyed by fault_id, so re-reporting the same
        id updates rather than duplicates) and invokes the handler
        registered for its severity exactly once."""
        with self._lock:
            self._active_faults[fault.fault_id] = fault
            handler = self._handlers.get(fault.severity)

        if handler is not None:
            handler(fault)

    def get_active_faults(self) -> List[Fault]:
        with self._lock:
            return [f for f in self._active_faults.values() if not f.resolved]

    def clear_fault(self, fault_id: str) -> bool:
        with self._lock:
            fault = self._active_faults.get(fault_id)
            if fault is None:
                return False
            fault.resolved = True
            fault.resolution_time = time.time()
            return True

    def highest_severity(self) -> FaultSeverity:
        active = self.get_active_faults()
        if not active:
            return FaultSeverity.INFO
        return max((f.severity for f in active), key=_SEVERITY_ORDER.index)
