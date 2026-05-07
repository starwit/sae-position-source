import pytest
from unittest.mock import patch, PropertyMock

from visionapi.sae_pb2 import PositionMessage

from positionsource.config import RedisConfig, SaePositionSourceConfig, GPSStaticConfig
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

def _deserialize(proto: bytes) -> PositionMessage:
    msg = PositionMessage()
    msg.ParseFromString(proto)
    return msg