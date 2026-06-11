#!/usr/bin/env python3
"""Shared data models for the River Song robotics foundation.

These types are robot-agnostic: they are used by every River Song unit
type (quadruped, manipulator-equipped, wheeled, aerial, ...) and by the
River Song API client. Platform-specific code lives under
locomotion/<platform>/ and hardware/.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PlatformType(Enum):
    """Top-level mobility platform. Selects the locomotion plugin a unit
    is wired up with at boot (see core/robot_factory.py)."""
    QUADRUPED = "QUADRUPED"
    WHEELED = "WHEELED"
    TRACKED = "TRACKED"
    AERIAL = "AERIAL"
    HUMANOID = "HUMANOID"
    STATIONARY = "STATIONARY"


class SensorType(Enum):
    """Physical sensor/actuator-bus categories a unit profile can declare.

    Each unit lists its actual sensors under "sensors" in units/*.json;
    the set and count of sensors varies freely per unit (see SensorSpec).
    """
    IMU = "IMU"
    GPS = "GPS"
    CAMERA = "CAMERA"
    LIDAR = "LIDAR"
    ULTRASONIC = "ULTRASONIC"
    FORCE_TORQUE = "FORCE_TORQUE"
    SERVO_BUS = "SERVO_BUS"
    BATTERY = "BATTERY"
    MICROPHONE = "MICROPHONE"
    ENCODER = "ENCODER"


class FaultSeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"


class LocomotionMode(Enum):
    IDLE = "IDLE"
    WALK = "WALK"
    TROT = "TROT"
    SIT = "SIT"
    STAND = "STAND"
    RTB = "RTB"
    MANIPULATING = "MANIPULATING"


class GaitType(Enum):
    WALK = "WALK"
    TROT = "TROT"
    SIT = "SIT"
    STAND = "STAND"


class TerrainType(Enum):
    FLAT = "FLAT"
    GRASS = "GRASS"
    GRAVEL = "GRAVEL"
    SLOPE = "SLOPE"
    ROUGH = "ROUGH"
    UNKNOWN = "UNKNOWN"


class PatrolPattern(Enum):
    PERIMETER = "PERIMETER"
    GRID = "GRID"
    RANDOM = "RANDOM"


class GPSFixQuality(Enum):
    NO_FIX = "NO_FIX"
    FIX_2D = "FIX_2D"
    FIX_3D = "FIX_3D"
    RTK = "RTK"


class CommandType(Enum):
    PATROL = "PATROL"
    RTB = "RTB"
    ESTOP = "ESTOP"
    SET_MODE = "SET_MODE"
    STREAM_START = "STREAM_START"
    STREAM_STOP = "STREAM_STOP"
    MANIPULATE = "MANIPULATE"


class CommandResult(Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED_EXPIRED = "REJECTED_EXPIRED"
    REJECTED_GEOFENCE = "REJECTED_GEOFENCE"
    REJECTED_UNIT_MISMATCH = "REJECTED_UNIT_MISMATCH"
    REJECTED_UNSUPPORTED = "REJECTED_UNSUPPORTED"


# ---------------------------------------------------------------------------
# Geometry / Navigation
# ---------------------------------------------------------------------------

@dataclass
class GPSCoordinate:
    latitude: float
    longitude: float
    altitude_m: float = 0.0
    accuracy_m: float = 0.0
    timestamp: float = 0.0

    def __post_init__(self):
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError(f"latitude out of range: {self.latitude}")
        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError(f"longitude out of range: {self.longitude}")
        if self.accuracy_m < 0.0:
            raise ValueError(f"accuracy_m must be >= 0: {self.accuracy_m}")


@dataclass
class SensorSpec:
    """Declarative description of one physical sensor/bus instance.

    Unit profiles list these under "sensors" so hardware/ drivers can be
    built generically by core/robot_factory.py: it looks up a registered
    factory by `sensor_type` and instantiates it with this spec, regardless
    of which platform or sensor mix a given unit has.
    """
    name: str
    sensor_type: SensorType
    interface: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeofenceBoundary:
    boundary_id: str
    unit_id: str
    vertices: List[GPSCoordinate]
    base_location: GPSCoordinate
    max_radius_m: float

    def __post_init__(self):
        if len(self.vertices) < 3:
            raise ValueError("GeofenceBoundary requires at least 3 vertices")
        if self.max_radius_m <= 0.0:
            raise ValueError("max_radius_m must be > 0")


# ---------------------------------------------------------------------------
# Faults
# ---------------------------------------------------------------------------

@dataclass
class Fault:
    fault_id: str
    subsystem: str
    severity: FaultSeverity
    message: str
    timestamp: float
    resolved: bool = False
    resolution_time: Optional[float] = None


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

@dataclass
class Alert:
    """Operator-facing notification dispatched to the River Song API.

    Per design.md P9, every dispatched alert must correspond to an active
    fault in the FaultManager registry (linked via fault_id).
    """
    alert_id: str
    fault_id: str
    severity: FaultSeverity
    message: str
    timestamp: float


# ---------------------------------------------------------------------------
# Vision
# ---------------------------------------------------------------------------

@dataclass
class Detection:
    class_name: str
    confidence: float
    bounding_box: Tuple[int, int, int, int]
    timestamp: float


# ---------------------------------------------------------------------------
# Manipulation (arm / end-effector)
# ---------------------------------------------------------------------------

@dataclass
class ArmPose:
    """Target pose for an articulated arm, relative to its base frame."""
    x_m: float
    y_m: float
    z_m: float
    roll_deg: float = 0.0
    pitch_deg: float = 0.0
    yaw_deg: float = 0.0
    gripper_open: bool = True


# ---------------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------------

@dataclass
class TelemetrySnapshot:
    unit_id: str
    timestamp: float
    position: Optional[GPSCoordinate]
    battery_pct: float
    battery_voltage: float
    locomotion_mode: LocomotionMode
    active_faults: List[str] = field(default_factory=list)
    detections: List[Detection] = field(default_factory=list)
    signal_strength_dbm: int = 0
    vpn_latency_ms: Optional[float] = None
    roll_deg: float = 0.0
    pitch_deg: float = 0.0
    heading_deg: float = 0.0


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@dataclass
class UnitCommand:
    command_id: str
    unit_id: str
    command_type: CommandType
    parameters: Dict[str, Any]
    issued_by: str
    timestamp: float
    expiry: Optional[float] = None

    def is_expired(self, now: float) -> bool:
        return self.expiry is not None and self.expiry <= now


@dataclass
class UnitStatus:
    unit_id: str
    state: str
    timestamp: float
    reason: Optional[str] = None
