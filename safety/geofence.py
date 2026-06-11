#!/usr/bin/env python3
"""Geofence enforcement.

Every navigation waypoint must be validated against the active geofence
before execution (design.md Correctness Properties P1-P3). A unit with no
boundary loaded is treated as out-of-bounds everywhere - fail-safe.
"""

import math
import threading
from typing import List, Optional

from core.geo import haversine_distance_m, to_local_xy_m
from core.models import GeofenceBoundary, GPSCoordinate


class Geofence:
    def __init__(self):
        self._lock = threading.Lock()
        self._boundary: Optional[GeofenceBoundary] = None

    def load_boundary(self, boundary: GeofenceBoundary) -> None:
        with self._lock:
            self._boundary = boundary

    def get_active_boundary(self) -> Optional[GeofenceBoundary]:
        with self._lock:
            return self._boundary

    def is_within_boundary(self, position: GPSCoordinate) -> bool:
        """Ray-casting polygon containment, gated by a fast haversine
        radius check (design.md Geofence Ray-Casting Algorithm)."""
        boundary = self.get_active_boundary()
        if boundary is None:
            return False

        if haversine_distance_m(position, boundary.base_location) > boundary.max_radius_m:
            return False

        return self._point_in_polygon(position, boundary.vertices)

    def distance_to_boundary(self, position: GPSCoordinate) -> float:
        """Distance from `position` to the nearest boundary edge, in
        meters. Returns 0.0 if no boundary is loaded."""
        boundary = self.get_active_boundary()
        if boundary is None:
            return 0.0

        vertices = boundary.vertices
        n = len(vertices)
        return min(
            self._point_to_segment_distance_m(position, vertices[i], vertices[(i + 1) % n])
            for i in range(n)
        )

    def validate_waypoint(self, waypoint: GPSCoordinate) -> bool:
        return self.is_within_boundary(waypoint)

    @staticmethod
    def _point_in_polygon(position: GPSCoordinate, vertices: List[GPSCoordinate]) -> bool:
        n = len(vertices)
        crossings = 0
        j = n - 1

        for i in range(n):
            vi = vertices[i]
            vj = vertices[j]

            if (vi.latitude > position.latitude) != (vj.latitude > position.latitude):
                x_intersect = (
                    (vj.longitude - vi.longitude)
                    * (position.latitude - vi.latitude)
                    / (vj.latitude - vi.latitude)
                    + vi.longitude
                )
                if position.longitude < x_intersect:
                    crossings += 1

            j = i

        return crossings % 2 == 1

    @staticmethod
    def _point_to_segment_distance_m(position: GPSCoordinate, v1: GPSCoordinate, v2: GPSCoordinate) -> float:
        ax, ay = to_local_xy_m(position, v1)
        bx, by = to_local_xy_m(position, v2)

        dx, dy = bx - ax, by - ay
        seg_len_sq = dx * dx + dy * dy
        if seg_len_sq == 0.0:
            return math.hypot(ax, ay)

        t = (-ax * dx - ay * dy) / seg_len_sq
        t = max(0.0, min(1.0, t))
        closest_x = ax + t * dx
        closest_y = ay + t * dy
        return math.hypot(closest_x, closest_y)
