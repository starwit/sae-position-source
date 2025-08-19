from typing import NamedTuple

class GpsPosition(NamedTuple):
    fix: bool
    lat: float
    lon: float
    hdop: float
    timestamp_utc_ms: int