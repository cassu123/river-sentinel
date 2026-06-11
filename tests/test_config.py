#!/usr/bin/env python3
import json

import pytest

from core.config import Config
from core.models import GeofenceBoundary, PlatformType


def test_default_profile_loads():
    config = Config()
    assert config.unit_id == "RS-001"
    assert config.platform_type == PlatformType.QUADRUPED
    assert config.has_capability("manipulator") is True
    assert config.has_capability("nonexistent_capability") is False


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
