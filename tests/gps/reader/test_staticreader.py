import time

from positionsource.gps.reader.staticreader import StaticReader


def test_static_reader():
    reader = StaticReader(lat=52.0, lon=12.0, read_interval_s=0.2)
    position = reader.position
    
    assert position is not None
    assert position.fix == True
    assert abs(position.lat - 52.0) < 1e-6
    assert abs(position.lon - 12.0) < 1e-6
    assert position.hdop == 0
    
    reader.close()

def test_monotonic_timestamps():
    reader = StaticReader(lat=52.0, lon=12.0, read_interval_s=0.2)
    position1 = reader.position
    position2 = reader.position
    
    assert position1 is not None
    assert position2 is not None
    assert position2.timestamp_utc_ms >= position1.timestamp_utc_ms  # Timestamps should be monotonic
    
    reader.close()