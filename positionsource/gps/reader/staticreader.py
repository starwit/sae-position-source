
import time
from typing import Optional

from ...datatypes import GpsPosition


class StaticReader:
    '''This class mimicks GPS reading by sending static configured position data.'''
    def __init__(self, lat: float, lon: float, read_interval_s: float):
        self._lat = lat
        self._lon = lon
        self._read_interval_s = read_interval_s
        
    @property
    def position(self) -> Optional[GpsPosition]:
        time.sleep(self._read_interval_s)
        return GpsPosition(fix=True, lat=self._lat, lon=self._lon, hdop=0, timestamp_utc_ms=int(time.time() * 1000))
    
    @property
    def is_alive(self) -> bool:
        return True
    
    def close(self):
        return True