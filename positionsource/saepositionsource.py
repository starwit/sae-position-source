import logging
import time
from typing import Any, Optional

from prometheus_client import Counter, Histogram, Summary
from visionapi.common_pb2 import MessageType
from visionapi.sae_pb2 import PositionMessage

from .gps.reader.commandreader import CommandGpsReader
from .config import (GPSCommandConfig, GPSFilterConfig, GPSStaticConfig,
                     SaePositionSourceConfig)
from .gps.reader.staticreader import StaticReader
from .datatypes import GpsPosition
from .gps.filter import GPSFilter

logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s %(processName)-10s %(message)s')
logger = logging.getLogger(__name__)

GET_DURATION = Histogram('sae_position_source_get_duration', 'The time it takes to deserialize the proto until returning the tranformed result as a serialized proto',
                         buckets=(0.0025, 0.005, 0.0075, 0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25))
OBJECT_COUNTER = Counter('sae_position_source_object_counter', 'How many detections have been transformed')
PROTO_SERIALIZATION_DURATION = Summary('sae_position_source_proto_serialization_duration', 'The time it takes to create a serialized output proto')


class SaePositionSource:
    def __init__(self, config: SaePositionSourceConfig) -> None:
        self.config = config
        logger.setLevel(self.config.log_level.value)
        self._gps_reader = None
        self._previous_position = None
        self._gps_filter = None
        if isinstance(self.config.gps_filter, GPSFilterConfig):
            self._gps_filter = GPSFilter(alpha=self.config.gps_filter.alpha, beta=self.config.gps_filter.beta, spike_radius_m=self.config.gps_filter.spike_radius_m)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __call__(self, input_proto) -> Any:
        return self.get(input_proto)

    def start(self):
        source_config = self.config.position_source
        if isinstance(source_config, GPSStaticConfig):
            logger.debug("Selecting static GPS reader")
            self._gps_reader = StaticReader(
                lat=source_config.lat, 
                lon=source_config.lon, 
                read_interval_s=source_config.read_interval_s
            )
        if isinstance(source_config, GPSCommandConfig):
            logger.debug("Selecting command GPS reader")
            self._gps_reader = CommandGpsReader(
                command=source_config.command, 
                read_timeout_s=source_config.read_timeout_s
            )
    
    @GET_DURATION.time()
    def get(self) -> Optional[PositionMessage]:
        '''This method returns a new PositionMessage if a new GPS position is available.
        If no new position is available before the timeout expires, it returns None.'''

        if self._gps_reader is None:
            return None
        
        if not self._gps_reader.is_alive:
            logger.error('GPS reader thread is not alive')
            return None

        current_position = self._gps_reader.position

        # Reset the gps filter if there is no position or no fix
        if self._gps_filter is not None and (current_position is None or current_position.fix == False):
            self._gps_filter.reset()

        if current_position is None:
            return None
        
        pos_msg = PositionMessage()
        pos_msg.fix = current_position.fix
        pos_msg.timestamp_utc_ms = current_position.timestamp_utc_ms
        pos_msg.type = MessageType.POSITION
        
        # Only feed filter and set coordinates if we have a valid GPS fix
        if current_position.fix == True:
            if self._gps_filter is not None:
                filter_result = self._gps_filter.update(current_position.lat, current_position.lon, current_position.timestamp_utc_ms)
                pos_msg.geo_coordinate.latitude = filter_result.lat
                pos_msg.geo_coordinate.longitude = filter_result.lon
                pos_msg.movement_vector.speed_kmh = filter_result.speed_kmh
                pos_msg.movement_vector.heading_deg = filter_result.heading_deg
            else:
                pos_msg.geo_coordinate.latitude = current_position.lat
                pos_msg.geo_coordinate.longitude = current_position.lon
            
            pos_msg.raw_geo_coordinate.latitude = current_position.lat
            pos_msg.raw_geo_coordinate.longitude = current_position.lon
            pos_msg.hdop = current_position.hdop

        return self._pack_proto(pos_msg)
    
    @PROTO_SERIALIZATION_DURATION.time()
    def _pack_proto(self, pos_msg: PositionMessage):
        return pos_msg.SerializeToString()
    
    def close(self):
        if self._gps_reader is not None:
            self._gps_reader.close()
            self._gps_reader = None