from pathlib import Path

from positionsource.config import GPSCommandConfig, SaePositionSourceConfig, GPSStaticConfig, SaePositionSourceConfig

def test_full_config():
    config = SaePositionSourceConfig.model_validate_json('''{
        "log_level": "DEBUG",
        "redis": {
            "host": "redis-server",
            "port": 6380,
            "stream_id": "test_stream",
            "output_stream_prefix": "test_prefix"
        },
        "position_source": {
            "type": "static",
            "lat": 52.000,
            "lon": 12.000,
            "read_interval_s": 1.0
        },
        "gps_filter": {
            "enabled": true,
            "alpha": 0.8,
            "beta": 0.05,
            "spike_radius_m": 100.0
        },
        "prometheus_port": 9000
    }''')

    assert config.log_level.value == 'DEBUG'
    assert config.redis.host == 'redis-server'
    assert config.redis.port == 6380
    assert config.redis.stream_id == 'test_stream'
    assert config.redis.output_stream_prefix == 'test_prefix'
    assert isinstance(config.position_source, GPSStaticConfig)
    assert config.position_source.lat == 52.000
    assert config.position_source.lon == 12.000
    assert config.position_source.read_interval_s == 1.0
    assert config.gps_filter.enabled == True
    assert config.gps_filter.alpha == 0.8
    assert config.gps_filter.beta == 0.05
    assert config.gps_filter.spike_radius_m == 100.0
    assert config.prometheus_port == 9000

def test_minimal_config_defaults():
    config = SaePositionSourceConfig.model_validate_json('''{
        "position_source": {
            "type": "static",
            "lat": 52.000,
            "lon": 12.000
        }
    }''')

    assert config.log_level.value == 'WARNING'
    assert config.redis.host == 'localhost'
    assert config.redis.port == 6379
    assert config.redis.stream_id == 'self'
    assert config.redis.output_stream_prefix == 'positionsource'
    assert isinstance(config.position_source, GPSStaticConfig)
    assert config.position_source.lat == 52.000
    assert config.position_source.lon == 12.000
    assert config.position_source.read_interval_s == 0.5
    assert config.gps_filter.enabled == False
    assert config.prometheus_port == 8000

def test_command_reader_config():
    config = SaePositionSourceConfig.model_validate_json('''{
        "position_source": {
            "type": "command",
            "command": ["echo", "test"]
        }
    }''')

    assert isinstance(config.position_source, GPSCommandConfig)
    assert config.position_source.command == ["echo", "test"]
    assert config.position_source.read_timeout_s == 2.0
