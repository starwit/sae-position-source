import pytest
from unittest.mock import patch

from positionsource.config import RedisConfig, SaePositionSourceConfig


@pytest.fixture(autouse=True)
def disable_prometheus():
    # We don't want to start the Prometheus server during tests
    with patch('rediswriter.stage.start_http_server'):
        yield

@pytest.fixture
def redis_publisher_mock():
    with patch('geomapper.stage.RedisPublisher') as mock_publisher:
        yield mock_publisher.return_value.__enter__.return_value


@pytest.fixture
def set_config():
    with patch('positionsource.stage.SaePositionSourceConfig') as mock_config:
        def _make_mock_config(stream_id: str, input_stream_prefix: str):
            mock_config.return_value = SaePositionSourceConfig(
                log_level='WARNING',
                redis=RedisConfig(
                    stream_id=stream_id,
                    input_stream_prefix=input_stream_prefix
                )
            )
        yield _make_mock_config
    