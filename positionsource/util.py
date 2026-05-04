import math
from typing import Tuple

EARTH_RADIUS = 6378137.0  # meters

def distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # use ll_to_xy to convert to local meters and then compute distance from origin
    dx, dy = ll_to_xy(lat1, lon1, lat2, lon2)
    return math.hypot(dx, dy)
    
def ll_to_xy(lat: float, lon: float, origin_lat: float, origin_lon: float) -> Tuple[float, float]:
    """
    Convert lat/lon to local meters
    """
    dlat = math.radians(lat - origin_lat)
    dlon = math.radians(lon - origin_lon)

    mean_lat = math.radians((lat + origin_lat) / 2)

    x = EARTH_RADIUS * dlon * math.cos(mean_lat)
    y = EARTH_RADIUS * dlat
    return x, y

def xy_to_ll(x: float, y: float, origin_lat: float, origin_lon: float) -> Tuple[float, float]:
    lat = origin_lat + math.degrees(y / EARTH_RADIUS)

    mean_lat = math.radians((lat + origin_lat) / 2)

    lon = origin_lon + math.degrees(
        x / (EARTH_RADIUS * math.cos(mean_lat))
    )

    return lat, lon