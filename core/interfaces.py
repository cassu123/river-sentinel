#!/usr/bin/env python3
"""Abstract interfaces for pluggable robot subsystems.

Every concrete driver/controller (quadruped gait, wheeled drive, arm
manipulator, Pi5 servo driver, ...) implements one of these interfaces.
core/robot_factory.py selects implementations based on the active unit
profile, so the safety, connectivity, and telemetry layers in this
foundation never need to know which physical platform they're running on.

Implementations land in later phases (locomotion/, hardware/); this module
defines the contracts they must satisfy.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional, Tuple

from core.models import ArmPose, GPSCoordinate, GPSFixQuality, LocomotionMode

if TYPE_CHECKING:
    import numpy as np


# ---------------------------------------------------------------------------
# Mobility
# ---------------------------------------------------------------------------

class LocomotionController(ABC):
    """Drives the robot's primary mobility (legs, wheels, tracks, rotors)."""

    @abstractmethod
    def initialize(self) -> bool: ...

    @abstractmethod
    def set_mode(self, mode: LocomotionMode) -> bool: ...

    @abstractmethod
    def get_mode(self) -> LocomotionMode: ...

    @abstractmethod
    def set_velocity(self, linear_x: float, linear_y: float, angular_z: float) -> None: ...

    @abstractmethod
    def step(self) -> None:
        """Advance one control-loop tick (compute and apply actuator commands)."""

    @abstractmethod
    def halt(self) -> None: ...

    @abstractmethod
    def is_stable(self) -> bool: ...


class Manipulator(ABC):
    """Controls an articulated arm/end-effector mounted on the robot."""

    @abstractmethod
    def initialize(self) -> bool: ...

    @abstractmethod
    def move_to_pose(self, pose: ArmPose) -> bool: ...

    @abstractmethod
    def open_gripper(self) -> None: ...

    @abstractmethod
    def close_gripper(self) -> None: ...

    @abstractmethod
    def stow(self) -> None: ...

    @abstractmethod
    def is_stowed(self) -> bool: ...

    @abstractmethod
    def emergency_relax(self) -> None: ...


# ---------------------------------------------------------------------------
# Hardware drivers
# ---------------------------------------------------------------------------

class ServoDriver(ABC):
    """Abstracts the actuator bus (e.g. Pi Pico over serial) for joint control."""

    @abstractmethod
    def initialize(self) -> bool: ...

    @abstractmethod
    def set_joint_angle(self, joint_id: int, angle_deg: float) -> None: ...

    @abstractmethod
    def set_all_joints(self, angles: List[float]) -> None: ...

    @abstractmethod
    def get_joint_angle(self, joint_id: int) -> float: ...

    @abstractmethod
    def enable_torque(self, joint_id: int) -> None: ...

    @abstractmethod
    def disable_torque(self, joint_id: int) -> None: ...

    @abstractmethod
    def emergency_relax(self) -> None: ...


class IMUDriver(ABC):
    @abstractmethod
    def initialize(self) -> bool: ...

    @abstractmethod
    def get_roll_pitch_yaw(self) -> Tuple[float, float, float]: ...

    @abstractmethod
    def get_angular_velocity(self) -> Tuple[float, float, float]: ...

    @abstractmethod
    def get_linear_acceleration(self) -> Tuple[float, float, float]: ...

    @abstractmethod
    def is_fallen(self) -> bool: ...

    @abstractmethod
    def get_timestamp(self) -> float: ...


class BatteryDriver(ABC):
    @abstractmethod
    def initialize(self) -> bool: ...

    @abstractmethod
    def get_voltage(self) -> float: ...

    @abstractmethod
    def get_state_of_charge(self) -> float:
        """Returns 0.0 - 100.0 percent."""

    @abstractmethod
    def get_estimated_runtime_minutes(self) -> float: ...


class CameraDriver(ABC):
    @abstractmethod
    def initialize(self, resolution: Tuple[int, int], fps: int) -> bool: ...

    @abstractmethod
    def capture_frame(self) -> Optional["np.ndarray"]: ...

    @abstractmethod
    def is_streaming(self) -> bool: ...


class GPSDriver(ABC):
    @abstractmethod
    def initialize(self) -> bool: ...

    @abstractmethod
    def get_position(self) -> Optional[GPSCoordinate]: ...

    @abstractmethod
    def get_heading(self) -> Optional[float]: ...

    @abstractmethod
    def get_fix_quality(self) -> GPSFixQuality: ...
