from positionsource.filter import GPSFilter
from positionsource.util import distance_m


def _track_iter():
    with open('tests/test_data/track.csv', 'r') as f:
        f.readline()  # skip header
        for line in f:
            ts, lat, lon = line.strip().split(',')
            yield float(ts), float(lat), float(lon)


def test_gps_filter():
    gps_filter = GPSFilter(alpha=0.7, beta=0.04, spike_radius_m=80.0)

    filtered_positions = []
    
    for ts, lat, lon in _track_iter():
        filter_result = gps_filter.update(lat, lon, timestamp_ms=ts)
        filtered_positions.append(filter_result)

    # Check maximum distance between input and filtered positions is less than 0.5m
    for (ts, lat, lon), filter_result in zip(_track_iter(), filtered_positions):
        dist = distance_m(lat, lon, filter_result.lat, filter_result.lon)
        assert dist < 0.5, f"Distance between input and filtered position too large ({dist}m)"
