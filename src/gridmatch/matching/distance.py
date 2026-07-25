"""Geographic helpers used only as commercial allocation preferences."""

from __future__ import annotations

import math

EARTH_RADIUS_KM = 6371.0088


def great_circle_distance_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    """Return haversine great-circle distance in kilometres."""
    lat_a, lon_a, lat_b, lon_b = map(
        math.radians,
        (latitude_a, longitude_a, latitude_b, longitude_b),
    )
    delta_latitude = lat_b - lat_a
    delta_longitude = lon_b - lon_a
    haversine = (
        math.sin(delta_latitude / 2) ** 2
        + math.cos(lat_a)
        * math.cos(lat_b)
        * math.sin(delta_longitude / 2) ** 2
    )
    return float(
        2
        * EARTH_RADIUS_KM
        * math.asin(min(1.0, math.sqrt(haversine)))
    )
