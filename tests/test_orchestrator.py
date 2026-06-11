#!/usr/bin/env python3
import time

import pytest

from core.config import Config
from core.models import Fault, FaultSeverity
from core.orchestrator import RiverCore


@pytest.fixture
def core():
    return RiverCore(Config())


def test_boots_with_safety_layer_armed(core):
    assert core.estop.is_armed()
    assert not core.estop.is_triggered()

    boundary = core.geofence.get_active_boundary()
    assert boundary is not None
    assert boundary.unit_id == core.config.unit_id


def test_tick_without_faults_keeps_watchdog_healthy(core):
    core.tick()
    assert core.watchdog.is_healthy()
    assert not core.is_rtb_requested()


def test_fatal_fault_triggers_estop_and_rtb(core):
    core.fault_manager.report_fault(Fault(
        fault_id="test-fatal",
        subsystem="test",
        severity=FaultSeverity.FATAL,
        message="simulated fatal fault",
        timestamp=time.time(),
    ))

    assert core.estop.is_triggered()
    assert core.is_rtb_requested()
    assert core.estop.get_trigger_reason() == "simulated fatal fault"


def test_critical_fault_requests_rtb_without_estop(core):
    core.fault_manager.report_fault(Fault(
        fault_id="test-critical",
        subsystem="battery_monitor",
        severity=FaultSeverity.CRITICAL,
        message="battery critical",
        timestamp=time.time(),
    ))

    assert core.is_rtb_requested()
    assert not core.estop.is_triggered()


def test_watchdog_timeout_reported_as_critical_fault(core):
    core.watchdog.register_subsystem("vision", timeout_s=0.0)
    time.sleep(0.001)

    core.tick()

    assert core.is_rtb_requested()
    assert any(f.subsystem == "vision" for f in core.fault_manager.get_active_faults())


def test_estop_triggered_skips_subsystem_ticks_but_keeps_core_heartbeat(core):
    core.estop.trigger(reason="manual stop", source="test")

    core.tick()

    assert core.watchdog.is_healthy()
