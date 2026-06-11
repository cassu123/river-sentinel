#!/usr/bin/env python3
"""Plugin registry for platform-specific subsystems.

Locomotion controllers, manipulators, and sensor drivers register
themselves here keyed by platform type / name / sensor type.
core/orchestrator.py asks this registry for the implementations a given
unit needs, based on its profile, so the safety, connectivity, and
telemetry layers never need to know which concrete robot they're running
on or what sensors it carries.

Sensor drivers are looked up per-entry in the unit profile's "sensors"
list (core.config.Config.sensors), so two units of the same platform type
can carry completely different sensor arrays without any code changes
here - only their units/*.json profile differs.

Concrete implementations are added in later phases (locomotion/quadruped,
locomotion/manipulator, hardware/...). Until a platform's plugin is
registered, factory lookups raise PlatformNotImplementedError so the
orchestrator can still boot in safety-only mode.
"""

from typing import Any, Callable, Dict

from core.interfaces import LocomotionController, Manipulator
from core.models import PlatformType, SensorSpec, SensorType


class PlatformNotImplementedError(RuntimeError):
    """Raised when no plugin is registered for a requested platform/name."""


_locomotion_registry: Dict[PlatformType, Callable[[dict], LocomotionController]] = {}
_manipulator_registry: Dict[str, Callable[[dict], Manipulator]] = {}
_sensor_driver_registry: Dict[SensorType, Callable[[SensorSpec], Any]] = {}


def register_locomotion_controller(
    platform_type: PlatformType, factory: Callable[[dict], LocomotionController]
) -> None:
    """Register a LocomotionController factory for a platform type.

    `factory` receives the unit's profile dict and returns an initialized
    (but not yet `.initialize()`d) controller instance.
    """
    _locomotion_registry[platform_type] = factory


def register_manipulator(name: str, factory: Callable[[dict], Manipulator]) -> None:
    """Register a Manipulator factory under a profile-referenced name
    (e.g. profile["manipulator"]["type"])."""
    _manipulator_registry[name] = factory


def build_locomotion_controller(platform_type: PlatformType, profile: dict) -> LocomotionController:
    factory = _locomotion_registry.get(platform_type)
    if factory is None:
        raise PlatformNotImplementedError(
            f"No locomotion controller registered for platform type {platform_type.value}"
        )
    return factory(profile)


def build_manipulator(name: str, profile: dict) -> Manipulator:
    factory = _manipulator_registry.get(name)
    if factory is None:
        raise PlatformNotImplementedError(f"No manipulator registered for '{name}'")
    return factory(profile)


def register_sensor_driver(sensor_type: SensorType, factory: Callable[[SensorSpec], Any]) -> None:
    """Register a driver factory for a sensor type.

    `factory` receives the unit's SensorSpec (name, interface, params) and
    returns an initialized (but not yet `.initialize()`d) driver instance.
    Each unit profile declares its own sensor list, so the same sensor
    type can be instantiated any number of times with different specs.
    """
    _sensor_driver_registry[sensor_type] = factory


def build_sensor_driver(spec: SensorSpec) -> Any:
    factory = _sensor_driver_registry.get(spec.sensor_type)
    if factory is None:
        raise PlatformNotImplementedError(
            f"No driver registered for sensor type {spec.sensor_type.value} (sensor '{spec.name}')"
        )
    return factory(spec)
