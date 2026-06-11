#!/usr/bin/env python3
import json

import pytest

from core.config import Config
from core.models import GeofenceBoundary, PlatformType, SensorSpec, SensorType


def test_default_profile_loads():
    config = Config()
    assert config.unit_id == "RS-001"
    assert config.platform_type == PlatformType.QUADRUPED
    assert config.has_capability("manipulator") is True
    assert config.has_capability("nonexistent_capability") is False


def test_default_profile_sensors():
    config = Config()
    sensors = config.sensors
    assert len(sensors) > 0
    assert all(isinstance(s, SensorSpec) for s in sensors)

    imu = config.get_sensor("imu_main")
    assert imu is not None
    assert imu.sensor_type == SensorType.IMU
    assert imu.interface == "i2c"

    servo_buses = config.sensors_of_type(SensorType.SERVO_BUS)
    assert len(servo_buses) == 2

    assert config.get_sensor("nonexistent_sensor") is None


def test_default_profile_geofence_boundary():
    config = Config()
    boundary = config.geofence_boundary
    assert isinstance(boundary, GeofenceBoundary)
    assert boundary.unit_id == config.unit_id
    assert len(boundary.vertices) >= 3
    assert boundary.max_radius_m > 0


def test_missing_profile_raises(tmp_path):
    missing = tmp_path / "does_not_exist.json"
    with pytest.raises(FileNotFoundError):
        Config(profile_path=str(missing))


def test_custom_profile_path(tmp_path):
    profile = {
        "unit_id": "RV-001",
        "platform_type": "WHEELED",
        "capabilities": {"locomotion": "wheeled", "manipulator": False},
        "safety": {
            "geofence": {
                "max_radius_m": 200,
                "base_location": {"latitude": 1.0, "longitude": 1.0},
                "vertices": [
                    {"latitude": 1.001, "longitude": 0.999},
                    {"latitude": 1.001, "longitude": 1.001},
                    {"latitude": 0.999, "longitude": 1.001},
                ],
            }
        },
    }
    profile_path = tmp_path / "wheeled_profile.json"
    profile_path.write_text(json.dumps(profile))

    config = Config(profile_path=str(profile_path))
    assert config.unit_id == "RV-001"
    assert config.platform_type == PlatformType.WHEELED
    assert config.has_capability("manipulator") is False

    boundary = config.geofence_boundary
    assert len(boundary.vertices) == 3
    assert boundary.max_radius_m == 200


def test_humanoid_profile_with_different_sensor_array(tmp_path):
    """Different unit types declare entirely different sensor arrays;
    the same Config/SensorSpec parsing must handle both without changes."""
    profile = {
        "unit_id": "RH-001",
        "platform_type": "HUMANOID",
        "capabilities": {"locomotion": "biped", "manipulator": True, "vision": True},
        "sensors": [
            {"name": "head_imu", "type": "IMU", "interface": "i2c", "params": {"address": "0x69"}},
            {"name": "left_eye_camera", "type": "CAMERA", "interface": "usb", "params": {"resolution": [1280, 720]}},
            {"name": "right_eye_camera", "type": "CAMERA", "interface": "usb", "params": {"resolution": [1280, 720]}},
            {"name": "left_foot_force", "type": "FORCE_TORQUE", "interface": "spi"},
            {"name": "right_foot_force", "type": "FORCE_TORQUE", "interface": "spi"},
            {"name": "torso_servo_bus", "type": "SERVO_BUS", "interface": "ethercat", "params": {"joint_count": 20}},
        ],
        "safety": {
            "geofence": {
                "max_radius_m": 50,
                "base_location": {"latitude": 2.0, "longitude": 2.0},
                "vertices": [
                    {"latitude": 2.001, "longitude": 1.999},
                    {"latitude": 2.001, "longitude": 2.001},
                    {"latitude": 1.999, "longitude": 2.001},
                ],
            }
        },
    }
    profile_path = tmp_path / "humanoid_profile.json"
    profile_path.write_text(json.dumps(profile))

    config = Config(profile_path=str(profile_path))
    assert config.platform_type == PlatformType.HUMANOID

    cameras = config.sensors_of_type(SensorType.CAMERA)
    assert {c.name for c in cameras} == {"left_eye_camera", "right_eye_camera"}

    feet = config.sensors_of_type(SensorType.FORCE_TORQUE)
    assert len(feet) == 2
    assert feet[0].params == {}

    assert config.sensors_of_type(SensorType.GPS) == []
