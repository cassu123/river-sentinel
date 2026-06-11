#!/usr/bin/env python3
"""Unit profile loader.

Loads a robot's profile (units/*.json) and exposes it as typed
configuration shared by every subsystem. The profile path can be
overridden with the RIVER_UNIT_PROFILE environment variable, which lets
the same codebase run different unit profiles (quadruped, wheeled, ...)
without code changes.
"""

import json
import os
from pathlib import Path
from typing import Any, List, Optional

from core.constants import GEOFENCE_LIMIT_M
from core.models import GeofenceBoundary, GPSCoordinate, PlatformType, SensorSpec, SensorType

DEFAULT_PROFILE_PATH = Path(__file__).resolve().parent.parent / "units" / "sentinel_profile.json"


class Config:
    def __init__(self, profile_path: Optional[str] = None):
        self.profile_path = Path(profile_path or os.environ.get("RIVER_UNIT_PROFILE", DEFAULT_PROFILE_PATH))
        self.data = self._load_profile()

    def _load_profile(self) -> dict:
        if not self.profile_path.exists():
            raise FileNotFoundError(f"Unit profile not found at {self.profile_path}")
        with open(self.profile_path, "r") as f:
            return json.load(f)

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        val: Any = self.data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
        return val if val is not None else default

    @property
    def unit_id(self) -> str:
        return self.get("unit_id", "UNKNOWN")

    @property
    def program(self) -> str:
        return self.get("program", "river-sentinel")

    @property
    def platform_type(self) -> PlatformType:
        return PlatformType(self.get("platform_type", PlatformType.QUADRUPED.value))

    @property
    def capabilities(self) -> dict:
        return self.get("capabilities", {})

    def has_capability(self, name: str) -> bool:
        return bool(self.capabilities.get(name, False))

    @property
    def sensors(self) -> List[SensorSpec]:
        """Declarative sensor inventory for this unit.

        Every unit lists whichever sensors it actually has under
        "sensors" in its profile; the list varies freely per unit
        (a quadruped's leg servo bus vs. a humanoid's foot force
        sensors, for example).
        """
        return [
            SensorSpec(
                name=entry["name"],
                sensor_type=SensorType(entry["type"]),
                interface=entry.get("interface", ""),
                params=entry.get("params", {}),
            )
            for entry in self.get("sensors", [])
        ]

    def get_sensor(self, name: str) -> Optional[SensorSpec]:
        for spec in self.sensors:
            if spec.name == name:
                return spec
        return None

    def sensors_of_type(self, sensor_type: SensorType) -> List[SensorSpec]:
        return [spec for spec in self.sensors if spec.sensor_type == sensor_type]

    @property
    def rth_enabled(self) -> bool:
        return self.get("safety.rth_enabled", True)

    @property
    def battery_critical_pct(self) -> float:
        return self.get("safety.battery_critical_pct", 15.0)

    @property
    def geofence_boundary(self) -> GeofenceBoundary:
        geofence = self.get("safety.geofence", {})
        base = geofence.get("base_location", {})
        base_location = GPSCoordinate(
            latitude=base.get("latitude", 0.0),
            longitude=base.get("longitude", 0.0),
            altitude_m=base.get("altitude_m", 0.0),
        )
        vertices = [
            GPSCoordinate(latitude=v["latitude"], longitude=v["longitude"])
            for v in geofence.get("vertices", [])
        ]
        return GeofenceBoundary(
            boundary_id=geofence.get("boundary_id", f"{self.unit_id}-default"),
            unit_id=self.unit_id,
            vertices=vertices,
            base_location=base_location,
            max_radius_m=geofence.get("max_radius_m", GEOFENCE_LIMIT_M),
        )
