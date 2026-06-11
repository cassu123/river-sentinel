#!/usr/bin/env python3
"""Geographic math utilities shared across safety and navigation modules.

Pure-Python implementations are used (no geopy dependency) so this module
has zero external dependencies and can run on any unit, including during
unit testing on a development machine.
"""

import math

from core.models import GPSCoordinate

EARTH_RADIUS_M = 6371000.0


def haversine_distance_m(a: GPSCoordinate, b: GPSCoordinate) -> float:
    """Great-circle distance between two GPS coordinates, in meters."""
    lat1, lon1 = math.radians(a.latitude), math.radians(a.longitude)
    lat2, lon2 = math.radians(b.latitude), math.radians(b.longitude)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))


def to_local_xy_m(origin: GPSCoordinate, point: GPSCoordinate) -> tuple[float, float]:
    """Project `point` onto a local east/north meter-plane centered at `origin`.

    Approximation valid for the geofence-scale distances (hundreds of
    meters) used by River Song units.
    """
    east = haversine_distance_m(origin, GPSCoordinate(latitude=origin.latitude, longitude=point.longitude))
    if point.longitude < origin.longitude:
        east = -east

    north = haversine_distance_m(origin, GPSCoordinate(latitude=point.latitude, longitude=origin.longitude))
    if point.latitude < origin.latitude:
        north = -north

    return east, north
