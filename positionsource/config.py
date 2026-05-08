from typing import Literal, List

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated
from visionlib.pipeline.settings import LogLevel, YamlConfigSettingsSource


class RedisConfig(BaseModel):
    host: str = 'localhost'
    port: Annotated[int, Field(ge=1, le=65536)] = 6379
    stream_id: str = 'self'
    output_stream_prefix: str = 'positionsource'

class GPSStaticConfig(BaseModel):
    type: Literal['static']
    lat: float = 0.0
    lon: float = 0.0
    read_interval_s: float = 0.5

class GPSCommandConfig(BaseModel):
    type: Literal['command']
    command: Annotated[List[str], Field(min_length=1)]
    read_timeout_s: float = 2

class GPSFilterConfig(BaseModel):
    enabled: Literal[True]
    alpha: Annotated[float, Field(ge=0.0, le=1.0)] = 0.70
    beta: Annotated[float, Field(ge=0.0, le=1.0)] = 0.04
    spike_radius_m: Annotated[float, Field(ge=0.0)] = 80.0

class GPSFilterConfigDisabled(BaseModel):
    enabled: Literal[False] = False

class SaePositionSourceConfig(BaseSettings):
    log_level: LogLevel = LogLevel.WARNING
    redis: RedisConfig = RedisConfig()
    position_source: GPSStaticConfig | GPSCommandConfig = Field(discriminator='type')
    gps_read_timeout_s: Annotated[float, Field(ge=0.0)] = 2.0
    gps_filter: GPSFilterConfig | GPSFilterConfigDisabled = Field(discriminator='enabled', default=GPSFilterConfigDisabled())
    prometheus_port: Annotated[int, Field(ge=1024, le=65536)] = 8000

    model_config = SettingsConfigDict(env_nested_delimiter='__')

    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
        return (init_settings, env_settings, YamlConfigSettingsSource(settings_cls), file_secret_settings)