#!/usr/bin/env python3
import pytest

from core import robot_factory
from core.models import PlatformType, SensorSpec, SensorType


@pytest.fixture(autouse=True)
def _clean_registries():
    """Each test mutates the module-level registries; reset around it so
    tests don't leak plugin registrations into each other."""
    saved = (
        dict(robot_factory._locomotion_registry),
        dict(robot_factory._manipulator_registry),
        dict(robot_factory._sensor_driver_registry),
    )
    yield
    robot_factory._locomotion_registry.clear()
    robot_factory._locomotion_registry.update(saved[0])
    robot_factory._manipulator_registry.clear()
    robot_factory._manipulator_registry.update(saved[1])
    robot_factory._sensor_driver_registry.clear()
    robot_factory._sensor_driver_registry.update(saved[2])


def test_unregistered_locomotion_raises():
    with pytest.raises(robot_factory.PlatformNotImplementedError):
        robot_factory.build_locomotion_controller(PlatformType.AERIAL, profile={})


def test_locomotion_controller_built_from_registered_factory():
    sentinel = object()
    robot_factory.register_locomotion_controller(
        PlatformType.QUADRUPED, lambda profile: sentinel
    )

    assert robot_factory.build_locomotion_controller(PlatformType.QUADRUPED, profile={}) is sentinel


def test_unregistered_manipulator_raises():
    with pytest.raises(robot_factory.PlatformNotImplementedError):
        robot_factory.build_manipulator("arm_5dof", profile={})


def test_manipulator_built_from_registered_factory():
    sentinel = object()
    robot_factory.register_manipulator("arm_5dof", lambda profile: sentinel)

    assert robot_factory.build_manipulator("arm_5dof", profile={}) is sentinel


def test_unregistered_sensor_driver_raises():
    spec = SensorSpec(name="head_imu", sensor_type=SensorType.IMU, interface="i2c")

    with pytest.raises(robot_factory.PlatformNotImplementedError):
        robot_factory.build_sensor_driver(spec)


def test_sensor_driver_built_per_spec_for_different_units():
    """The same SensorType registration must work for arbitrarily many
    sensor instances, each with its own spec (different units, different
    sensor counts/positions)."""
    built = []
    robot_factory.register_sensor_driver(
        SensorType.FORCE_TORQUE, lambda spec: built.append(spec) or spec.name
    )

    left = SensorSpec(name="left_foot_force", sensor_type=SensorType.FORCE_TORQUE, interface="spi")
    right = SensorSpec(name="right_foot_force", sensor_type=SensorType.FORCE_TORQUE, interface="spi")

    assert robot_factory.build_sensor_driver(left) == "left_foot_force"
    assert robot_factory.build_sensor_driver(right) == "right_foot_force"
    assert built == [left, right]
