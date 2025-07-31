
import time
from typing import Optional

from positionsource.gpsreader import GpsPosition


class StaticReader:
    '''This class mimicks GPS reading by sending static configured position data.'''
    def __init__(self, long, lat):
        self._long = long
        self._lat = lat
        
    @property
    def position(self) -> Optional[GpsPosition]:
        time.sleep(0.5)
        return GpsPosition(fix=True, lat=self._lat, lon=self._long, hdop=0, timestamp_utc_ms=int(time.time() * 1000))
    
    @property
    def is_alive(self) -> bool:
        return True
    
    def close(self):
        return True