import logging
import time
from typing import Any, Optional

from prometheus_client import Counter, Histogram, Summary
from visionapi.common_pb2 import MessageType
from visionapi.sae_pb2 import PositionMessage

from .commandreader import CommandGpsReader
from .config import (GPSCommandConfig, GPSSerialConfig, GPSStaticConfig,
                     SaePositionSourceConfig)
from .serialreader import SerialGpsReader
from .staticreader import StaticReader

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

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __call__(self, input_proto) -> Any:
        return self.get(input_proto)

    def start(self):
        if isinstance(self.config.position_source, GPSStaticConfig):
            logger.debug("Selecting static GPS reader")
            self._gps_reader = StaticReader(self.config.position_source.lat, self.config.position_source.lon)
        if isinstance(self.config.position_source, GPSSerialConfig):
            logger.debug("Selecting dynamic GPS reader")
            self._gps_reader = SerialGpsReader(self.config.position_source.serial_device)
        if isinstance(self.config.position_source, GPSCommandConfig):
            logger.debug("Selecting command GPS reader")
            self._gps_reader = CommandGpsReader(self.config.position_source.command)
    
    @GET_DURATION.time()
    def get(self, timeout=1) -> Optional[PositionMessage]:
        '''This method returns a new PositionMessage if a new GPS position is available.
        If no new position is available before the timeout expires, it returns None.'''

        if self._gps_reader is None:
            return None
        
        if not self._gps_reader.is_alive:
            raise RuntimeError('GPS reader thread has exited')
        
        timeout_time = time.time() + timeout
        
        current_position = self._gps_reader.position

        # Retry until either the position changes or the timeout expires
        while timeout_time - time.time() > 0 and current_position == self._previous_position:
            time.sleep(0.01)
            current_position = self._gps_reader.position

        if current_position is None or current_position == self._previous_position:
            return None
        
        self._previous_position = current_position
        
        logger.debug(current_position)
        
        pos_msg = PositionMessage()
        pos_msg.fix = current_position.fix
        pos_msg.geo_coordinate.latitude = current_position.lat
        pos_msg.geo_coordinate.longitude = current_position.lon
        pos_msg.hdop = current_position.hdop
        pos_msg.timestamp_utc_ms = current_position.timestamp_utc_ms
        pos_msg.type = MessageType.POSITION

        return self._pack_proto(pos_msg)
        
    @PROTO_SERIALIZATION_DURATION.time()
    def _pack_proto(self, pos_msg: PositionMessage):
        return pos_msg.SerializeToString()
    
    def close(self):
        if self._gps_reader is not None:
            self._gps_reader.close()
            self._gps_reader = None