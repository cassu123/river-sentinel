#!/usr/bin/env python3
# River Sentinel - Autonomous Quadruped Security System

import time

from hypothesis import given, strategies as st

from core.models import Fault, FaultSeverity, GeofenceBoundary, GPSCoordinate
from safety.estop import EStop
from safety.fault_manager import FaultManager
from safety.geofence import Geofence
from safety.watchdog import Watchdog


# ---------------------------------------------------------------------------
# E-Stop
# ---------------------------------------------------------------------------

def test_estop_starts_unarmed_and_untriggered():
    estop = EStop()
    assert not estop.is_armed()
    assert not estop.is_triggered()


def test_estop_trigger_records_reason_and_source():
    estop = EStop()
    estop.arm()
    estop.trigger(reason="low battery", source="battery_monitor")
    assert estop.is_triggered()
    assert estop.get_trigger_reason() == "low battery"
    assert estop.get_trigger_source() == "battery_monitor"


def test_estop_reset_without_token_clears_trigger():
    estop = EStop()
    estop.trigger(reason="test", source="test")
    assert estop.reset() is True
    assert not estop.is_triggered()
    assert estop.get_trigger_reason() is None


def test_estop_reset_requires_matching_token_when_configured():
    estop = EStop(reset_token="secret")
    estop.trigger(reason="test", source="test")

    assert estop.reset(auth_token="wrong") is False
    assert estop.is_triggered()

    assert estop.reset(auth_token="secret") is True
    assert not estop.is_triggered()


# ---------------------------------------------------------------------------
# Watchdog
# ---------------------------------------------------------------------------

def test_watchdog_healthy_immediately_after_registration():
    fake_time = [0.0]
    watchdog = Watchdog(time_fn=lambda: fake_time[0])
    watchdog.register_subsystem("core", timeout_s=1.0)
    assert watchdog.is_healthy()
    assert watchdog.check_all() == []


def test_watchdog_detects_timeout():
    fake_time = [0.0]
    watchdog = Watchdog(time_fn=lambda: fake_time[0])
    watchdog.register_subsystem("vision", timeout_s=1.0)

    fake_time[0] = 0.5
    watchdog.heartbeat("vision")
    assert watchdog.is_healthy()

    fake_time[0] = 2.0
    assert watchdog.check_all() == ["vision"]
    assert not watchdog.is_healthy()


def test_watchdog_heartbeat_for_unknown_subsystem_raises():
    watchdog = Watchdog()
    try:
        watchdog.heartbeat("unknown")
        assert False, "expected KeyError"
    except KeyError:
        pass


# ---------------------------------------------------------------------------
# Fault Manager
# ---------------------------------------------------------------------------

def test_fault_manager_invokes_handler_for_severity():
    manager = FaultManager()
    received = []
    manager.register_handler(FaultSeverity.CRITICAL, received.append)

    fault = Fault(
        fault_id="f1",
        subsystem="battery_monitor",
        severity=FaultSeverity.CRITICAL,
        message="low battery",
        timestamp=time.time(),
    )
    manager.report_fault(fault)

    assert received == [fault]
    assert manager.get_active_faults() == [fault]


def test_fault_manager_does_not_duplicate_fault_ids():
    manager = FaultManager()

    manager.report_fault(Fault(
        fault_id="dup", subsystem="gps", severity=FaultSeverity.WARNING,
        message="first", timestamp=time.time(),
    ))
    manager.report_fault(Fault(
        fault_id="dup", subsystem="gps", severity=FaultSeverity.WARNING,
        message="second", timestamp=time.time(),
    ))

    active = manager.get_active_faults()
    assert len(active) == 1
    assert active[0].message == "second"


def test_fault_manager_clear_fault_resolves_it():
    manager = FaultManager()
    manager.report_fault(Fault(
        fault_id="f1", subsystem="gps", severity=FaultSeverity.WARNING,
        message="gps drift", timestamp=time.time(),
    ))

    assert manager.clear_fault("f1") is True
    assert manager.get_active_faults() == []
    assert manager.clear_fault("does-not-exist") is False


def test_fault_manager_highest_severity():
    manager = FaultManager()
    assert manager.highest_severity() == FaultSeverity.INFO

    manager.report_fault(Fault(
        fault_id="f1", subsystem="gps", severity=FaultSeverity.WARNING,
        message="gps drift", timestamp=time.time(),
    ))
    manager.report_fault(Fault(
        fault_id="f2", subsystem="imu", severity=FaultSeverity.FATAL,
        message="imu offline", timestamp=time.time(),
    ))

    assert manager.highest_severity() == FaultSeverity.FATAL


# ---------------------------------------------------------------------------
# Geofence
# ---------------------------------------------------------------------------

def _square_boundary(half_size_deg=0.001, max_radius_m=1000.0) -> GeofenceBoundary:
    base = GPSCoordinate(latitude=0.0, longitude=0.0)
    vertices = [
        GPSCoordinate(latitude=half_size_deg, longitude=-half_size_deg),
        GPSCoordinate(latitude=half_size_deg, longitude=half_size_deg),
        GPSCoordinate(latitude=-half_size_deg, longitude=half_size_deg),
        GPSCoordinate(latitude=-half_size_deg, longitude=-half_size_deg),
    ]
    return GeofenceBoundary(
        boundary_id="test", unit_id="TEST", vertices=vertices,
        base_location=base, max_radius_m=max_radius_m,
    )


def test_geofence_with_no_boundary_is_fail_safe_out_of_bounds():
    geofence = Geofence()
    position = GPSCoordinate(latitude=0.0, longitude=0.0)
    assert geofence.is_within_boundary(position) is False
    assert geofence.distance_to_boundary(position) == 0.0
    assert geofence.get_active_boundary() is None


def test_geofence_point_inside_polygon_and_radius():
    geofence = Geofence()
    geofence.load_boundary(_square_boundary())

    center = GPSCoordinate(latitude=0.0, longitude=0.0)
    assert geofence.is_within_boundary(center) is True
    assert geofence.validate_waypoint(center) is True
    assert geofence.distance_to_boundary(center) > 0.0


def test_geofence_point_outside_polygon_is_rejected():
    geofence = Geofence()
    geofence.load_boundary(_square_boundary())

    outside = GPSCoordinate(latitude=0.01, longitude=0.01)
    assert geofence.is_within_boundary(outside) is False


@given(
    lat_offset=st.floats(min_value=1.0, max_value=10.0),
    lon_offset=st.floats(min_value=1.0, max_value=10.0),
)
def test_points_far_outside_radius_are_never_within_boundary(lat_offset, lon_offset):
    """Property P-style check: anything beyond max_radius_m is rejected by
    the fast haversine path before polygon containment is even considered."""
    geofence = Geofence()
    geofence.load_boundary(_square_boundary())

    position = GPSCoordinate(latitude=lat_offset, longitude=lon_offset)
    assert geofence.is_within_boundary(position) is False
