#!/usr/bin/env python3
import math

from core.geo import haversine_distance_m, to_local_xy_m
from core.models import GPSCoordinate


def test_haversine_distance_zero_for_identical_points():
    a = GPSCoordinate(latitude=37.0, longitude=-122.0)
    assert haversine_distance_m(a, a) == 0.0


def test_haversine_distance_one_degree_latitude_is_about_111km():
    a = GPSCoordinate(latitude=0.0, longitude=0.0)
    b = GPSCoordinate(latitude=1.0, longitude=0.0)
    distance = haversine_distance_m(a, b)
    assert 110_000.0 < distance < 112_000.0


def test_to_local_xy_m_signs_match_compass_directions():
    origin = GPSCoordinate(latitude=0.0, longitude=0.0)

    east, north = to_local_xy_m(origin, GPSCoordinate(latitude=0.0, longitude=0.001))
    assert east > 0
    assert math.isclose(north, 0.0, abs_tol=1e-6)

    east, north = to_local_xy_m(origin, GPSCoordinate(latitude=0.001, longitude=0.0))
    assert math.isclose(east, 0.0, abs_tol=1e-6)
    assert north > 0

    east, north = to_local_xy_m(origin, GPSCoordinate(latitude=-0.001, longitude=-0.001))
    assert east < 0
    assert north < 0
