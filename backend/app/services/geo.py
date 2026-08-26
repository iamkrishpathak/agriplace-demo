from math import asin, cos, radians, sin, sqrt


ROAD_FACTOR = 1.28


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return 2 * radius_km * asin(sqrt(a))


def derived_road_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return round(haversine_km(lat1, lon1, lat2, lon2) * ROAD_FACTOR, 2)

