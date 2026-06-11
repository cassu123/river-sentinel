#!/usr/bin/env python3
"""Plugin registry for platform-specific subsystems.

Locomotion controllers and manipulators register themselves here keyed
by platform type / name. core/orchestrator.py asks this registry for the
implementations a given unit needs, based on its profile, so the safety,
connectivity, and telemetry layers never need to know which concrete
robot they're running on.

Concrete implementations are added in later phases (locomotion/quadruped,
locomotion/manipulator, ...). Until a platform's plugin is registered,
factory lookups raise PlatformNotImplementedError so the orchestrator can
still boot in safety-only mode.
"""

from typing import Callable, Dict

from core.interfaces import LocomotionController, Manipulator
from core.models import PlatformType


class PlatformNotImplementedError(RuntimeError):
    """Raised when no plugin is registered for a requested platform/name."""


_locomotion_registry: Dict[PlatformType, Callable[[dict], LocomotionController]] = {}
_manipulator_registry: Dict[str, Callable[[dict], Manipulator]] = {}


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
