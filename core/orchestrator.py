#!/usr/bin/env python3
"""Robot-agnostic boot sequence and control loop.

This module has no ROS2 or hardware dependencies, so it can be unit
tested directly. core/main.py wraps RiverCore in a ROS2 node and calls
tick() on a timer.

Hardware, locomotion, navigation, vision, and connectivity subsystems are
wired in via core/robot_factory.py in later phases. Until a platform's
plugins are registered, RiverCore still boots and runs in safety-only
mode: the geofence, watchdog, and fault manager are live and the E-Stop
can be triggered and observed.
"""

import logging
import time

from core.config import Config
from core.constants import CONTROL_LOOP_PERIOD_S
from core.models import Fault, FaultSeverity
from safety.estop import EStop
from safety.fault_manager import FaultManager
from safety.geofence import Geofence
from safety.watchdog import Watchdog

logger = logging.getLogger(__name__)

CORE_WATCHDOG_TIMEOUT_S = CONTROL_LOOP_PERIOD_S * 5


class RiverCore:
    """Owns the safety layer and main control loop for a single unit."""

    def __init__(self, config: Config):
        self.config = config
        self.estop = EStop()
        self.watchdog = Watchdog()
        self.geofence = Geofence()
        self.fault_manager = FaultManager()

        self._rtb_requested = False

        self._initialize_safety()

    def _initialize_safety(self) -> None:
        """Boot order: E-Stop armed, geofence loaded, watchdog and fault
        handlers registered - before any other subsystem starts
        (design.md Boot Sequence / Correctness Property P4)."""
        self.estop.arm()
        self.geofence.load_boundary(self.config.geofence_boundary)
        self.watchdog.register_subsystem("core", timeout_s=CORE_WATCHDOG_TIMEOUT_S)

        self.fault_manager.register_handler(FaultSeverity.FATAL, self._handle_fatal)
        self.fault_manager.register_handler(FaultSeverity.CRITICAL, self._handle_critical)
        self.fault_manager.register_handler(FaultSeverity.WARNING, self._handle_warning)
        self.fault_manager.register_handler(FaultSeverity.INFO, self._handle_info)

        logger.info(
            "Safety layer initialized for unit %s (%s)",
            self.config.unit_id,
            self.config.platform_type.value,
        )

    def _handle_fatal(self, fault: Fault) -> None:
        logger.critical("FATAL fault [%s]: %s", fault.subsystem, fault.message)
        self.estop.trigger(reason=fault.message, source=fault.subsystem)
        self._rtb_requested = True

    def _handle_critical(self, fault: Fault) -> None:
        logger.error("CRITICAL fault [%s]: %s", fault.subsystem, fault.message)
        self._rtb_requested = True

    def _handle_warning(self, fault: Fault) -> None:
        logger.warning("WARNING fault [%s]: %s", fault.subsystem, fault.message)

    def _handle_info(self, fault: Fault) -> None:
        logger.info("INFO fault [%s]: %s", fault.subsystem, fault.message)

    def is_rtb_requested(self) -> bool:
        return self._rtb_requested

    def tick(self) -> None:
        """Run one iteration of the safety-first control loop."""
        for subsystem in self.watchdog.check_all():
            self.fault_manager.report_fault(Fault(
                fault_id=f"watchdog-{subsystem}",
                subsystem=subsystem,
                severity=FaultSeverity.CRITICAL,
                message=f"Watchdog timeout: {subsystem}",
                timestamp=time.time(),
            ))

        if self.estop.is_triggered():
            self.watchdog.heartbeat("core")
            return

        # Hardware, locomotion, navigation, vision, and connectivity ticks
        # are added here in later phases via core/robot_factory.py.

        self.watchdog.heartbeat("core")
