
import enum
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated
from visionlib.pipeline.settings import LogLevel, YamlConfigSettingsSource


class RedisConfig(BaseModel):
    host: str = 'localhost'
    port: Annotated[int, Field(ge=1, le=65536)] = 6379
    stream_id: str = 'self'
    output_stream_prefix: str = 'positionsource'

class GPSSourceConfig(BaseModel):
    serial_device: Path = Path('/dev/ttyACM0')
    long: float = 0.0
    lat: float = 0.0

class GPSConfig(BaseModel):
    serial_device: Path = Path('/dev/ttyACM0')

class PositionDataSourceConfig(BaseModel):
    type: str = 'static'
    gps_source: GPSSourceConfig = Field(default_factory=GPSSourceConfig)

class SaePositionSourceConfig(BaseSettings):
    log_level: LogLevel = LogLevel.WARNING
    redis: RedisConfig = RedisConfig()
    position_data_source: PositionDataSourceConfig
    prometheus_port: Annotated[int, Field(ge=1024, le=65536)] = 8000

    model_config = SettingsConfigDict(env_nested_delimiter='__')

    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
        return (init_settings, env_settings, YamlConfigSettingsSource(settings_cls), file_secret_settings)