import logging
import signal
import threading

from prometheus_client import Histogram, start_http_server
from visionlib.pipeline.publisher import RedisPublisher

from .config import SaePositionSourceConfig
from .saepositionsource import SaePositionSource

logger = logging.getLogger(__name__)

REDIS_PUBLISH_DURATION = Histogram('sae_position_source_redis_publish_duration', 'The time it takes to push a message onto the Redis stream',
                                   buckets=(0.0025, 0.005, 0.0075, 0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25))

def run_stage():

    stop_event = threading.Event()

    # Register signal handlers
    def sig_handler(signum, _):
        signame = signal.Signals(signum).name
        print(f'Caught signal {signame} ({signum}). Exiting...')
        stop_event.set()

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    # Load config from settings.yaml / env vars
    CONFIG = SaePositionSourceConfig()

    logger.setLevel(CONFIG.log_level.value)

    logger.info(f'Starting prometheus metrics endpoint on port {CONFIG.prometheus_port}')

    start_http_server(CONFIG.prometheus_port)

    logger.info(f'Starting geo mapper stage. Config: {CONFIG.model_dump_json(indent=2)}')

    sae_position_source = SaePositionSource(CONFIG)

    publish = RedisPublisher(CONFIG.redis.host, CONFIG.redis.port)
    
    with publish:
        while True:
            if stop_event.is_set():
                break

            output_proto_data = sae_position_source.get()

            if output_proto_data is None:
                continue
            
            with REDIS_PUBLISH_DURATION.time():
                publish(f'{CONFIG.redis.output_stream_prefix}:{CONFIG.redis.stream_id}', output_proto_data)
            