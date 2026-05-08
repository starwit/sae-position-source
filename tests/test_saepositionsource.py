import pytest
from unittest.mock import patch, PropertyMock

from visionapi.sae_pb2 import PositionMessage

from positionsource.config import GPSFilterConfig, RedisConfig, SaePositionSourceConfig, GPSStaticConfig
from positionsource.datatypes import GpsPosition
from positionsource.saepositionsource import SaePositionSource


@pytest.fixture
def config():
    return SaePositionSourceConfig(
        log_level='WARNING',
        redis=RedisConfig(
            stream_id='stream1',
            output_stream_prefix='positionsource',
        ),
        position_source=GPSStaticConfig(
            type='static',
            lat=52.0,
            lon=13.0
        )
    )

@pytest.fixture
def inject_position_readings():
    with patch('positionsource.saepositionsource.StaticReader.position', new_callable=PropertyMock) as mock_position:
        def _inject_messages(gps_positions: list[GpsPosition]):
            mock_position.side_effect = gps_positions
        yield _inject_messages

def test_read_single(inject_position_readings, config):
    inject_position_readings([
        GpsPosition(fix=True, lat=52.0, lon=13.0, hdop=1.0, timestamp_utc_ms=1000)
    ])

    with SaePositionSource(config) as position_source:
        output = position_source.get()

        assert output is not None
        msg = _deserialize(output)
        assert msg.fix == True
        assert msg.geo_coordinate.latitude == 52.0
        assert msg.geo_coordinate.longitude == 13.0
        assert msg.timestamp_utc_ms == 1000

def test_read_multiple(inject_position_readings, config):
    inject_position_readings([
        GpsPosition(fix=True, lat=52.0, lon=13.0, hdop=1.0, timestamp_utc_ms=1000),
        GpsPosition(fix=True, lat=52.1, lon=13.1, hdop=1.0, timestamp_utc_ms=2000),
        GpsPosition(fix=False, lat=0.0, lon=0.0, hdop=0.0, timestamp_utc_ms=3000)
    ])

    with SaePositionSource(config) as position_source:
        output1 = position_source.get()
        output2 = position_source.get()
        output3 = position_source.get()

        assert output1 is not None
        msg1 = _deserialize(output1)
        assert msg1.fix == True
        assert msg1.geo_coordinate.latitude == 52.0
        assert msg1.geo_coordinate.longitude == 13.0
        assert msg1.timestamp_utc_ms == 1000

        assert output2 is not None
        msg2 = _deserialize(output2)
        assert msg2.fix == True
        assert msg2.geo_coordinate.latitude == 52.1
        assert msg2.geo_coordinate.longitude == 13.1
        assert msg2.timestamp_utc_ms == 2000

        assert output3 is not None
        msg3 = _deserialize(output3)
        assert msg3.fix == False
        assert msg3.geo_coordinate.latitude == 0.0
        assert msg3.geo_coordinate.longitude == 0.0
        assert msg3.timestamp_utc_ms == 3000

def test_no_reading(inject_position_readings, config):
    inject_position_readings([
        None
    ])

    with SaePositionSource(config) as position_source:
        output = position_source.get()

        assert output is None

def test_active_filter(inject_position_readings, config):
    config.gps_filter = GPSFilterConfig(enabled=True, alpha=0.7, beta=0.04, spike_radius_m=100.0)

    track = [
        GpsPosition(fix=True, lat=52.40868945371039452, lon=10.780447239674544, hdop=1.0, timestamp_utc_ms=1000),
        GpsPosition(fix=True, lat=52.40874910760433652, lon=10.78034945034642,  hdop=1.0, timestamp_utc_ms=1200),
        GpsPosition(fix=True, lat=52.40881591986982452, lon=10.7802594841651,   hdop=1.0, timestamp_utc_ms=1400),
        GpsPosition(fix=True, lat=52.4088803458874452,  lon=10.780204722141349, hdop=1.0, timestamp_utc_ms=1600),
        GpsPosition(fix=True, lat=52.4089423856671352,  lon=10.780165606410463, hdop=1.0, timestamp_utc_ms=1800),
        GpsPosition(fix=True, lat=52.4090020392189652,  lon=10.780142136971563, hdop=1.0, timestamp_utc_ms=2000),
        GpsPosition(fix=True, lat=52.40904498972642552, lon=10.78013040225295,  hdop=1.0, timestamp_utc_ms=2200),
        GpsPosition(fix=True, lat=52.40906885110186452, lon=10.780122579106092, hdop=1.0, timestamp_utc_ms=2400),
        GpsPosition(fix=True, lat=52.4090950985990452,  lon=10.780118667533486, hdop=1.0, timestamp_utc_ms=2600),
        GpsPosition(fix=True, lat=52.4091261183487552,  lon=10.780118667533486, hdop=1.0, timestamp_utc_ms=2800),
        GpsPosition(fix=True, lat=52.4091547519448752,  lon=10.780110844387508, hdop=1.0, timestamp_utc_ms=3000),
        GpsPosition(fix=True, lat=52.40922156359590652, lon=10.780110844387508, hdop=1.0, timestamp_utc_ms=3200),
        GpsPosition(fix=True, lat=52.4093050780178452,  lon=10.780122579106092, hdop=1.0, timestamp_utc_ms=3400),
        GpsPosition(fix=True, lat=52.4093766616817652,  lon=10.780149960118393, hdop=1.0, timestamp_utc_ms=3600),
        GpsPosition(fix=True, lat=52.4094959675306652,  lon=10.780200810568772, hdop=1.0, timestamp_utc_ms=3800),
    ]

    inject_position_readings(track)

    output_msgs = []

    with SaePositionSource(config) as position_source:
        for _ in range(len(track)):
            output_msgs.append(position_source.get())

    # Discard the first reading to let the filter initialize, then check that the following readings are filtered but still approximately correct
    for gps_position, output in zip(track[1:], output_msgs[1:]):

        assert output is not None
        msg = _deserialize(output)
        assert msg.fix == True
        assert msg.timestamp_utc_ms == gps_position.timestamp_utc_ms

        # Make sure the filter is active by checking that the output coordinates are not exactly the same as the input coordinates, but still approximately correct
        assert msg.geo_coordinate.latitude != gps_position.lat
        assert msg.geo_coordinate.longitude != gps_position.lon
        assert msg.geo_coordinate.latitude == pytest.approx(gps_position.lat, abs=0.0001)
        assert msg.geo_coordinate.longitude == pytest.approx(gps_position.lon, abs=0.0001)

        # Make sure heading and speed are non zero and within a reasonable range (for the input track)
        assert 0.0 <= msg.movement_vector.speed_kmh <= 70.0
        assert 300.0 <= msg.movement_vector.heading_deg <= 360.0

def _deserialize(proto: bytes) -> PositionMessage:
    msg = PositionMessage()
    msg.ParseFromString(proto)
    return msg