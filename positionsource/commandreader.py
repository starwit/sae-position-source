import logging
import os
import subprocess
import time
from threading import Event, Lock, Thread
from typing import List, Optional

from pynmeagps import NMEAMessage, NMEAReader

from .datatypes import GpsPosition

logger = logging.getLogger(__name__)

class CommandGpsError(Exception):
    pass

class CommandGpsReader:
    '''This class reads GPS data from a serial device and provides the latest position. It uses a separate thread to read data continuously.
        It needs to be closed properly to release the serial port.'''
    def __init__(self, command: List[str]):
        self._stop_event = Event()
        self._current_position: GpsPosition = None
        self._read_thread: Thread = Thread(target=self._gps_read_loop, kwargs={'command': command, 'stop_event': self._stop_event}, daemon=True)
        self._last_position_lock = Lock()
        self._read_thread.start()

    def _gps_read_loop(self, command: List[str], stop_event: Event):
        '''This method runs in a separate thread. Do not call it directly.'''
        try:
            proc = None
            while not stop_event.is_set():
                if proc is None:
                    proc = subprocess.Popen(args=command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    # We don't want to block on stderr reads
                    os.set_blocking(proc.stderr.fileno(), False)
                    logger.debug(f'Started gps reader subprocess with command {" ".join(command)}')
                    time.sleep(0.5)

                # Check if the started process is still alive
                if (ret_code := proc.poll()) is not None:
                    logger.warning(f'Subprocess has ended with code {ret_code}. Restarting...)')
                    self._log_multiline_output(proc.stderr.readlines(), 'stderr', logging.WARNING)
                    proc = None
                    time.sleep(1)
                    continue

                # Retrieve stderr output (to make sure the buffer does not fill up) and display for informational purposes
                stderr_lines = proc.stderr.readlines()
                if len(stderr_lines) > 0:
                    self._log_multiline_output(stderr_lines, 'stderr', logging.WARNING)

                line = proc.stdout.readline()
                if not line.startswith(b'$'):
                    continue

                nmea: NMEAMessage = NMEAReader.parse(line)
                if nmea.msgID != 'GGA':
                    continue

                new_position = GpsPosition(
                    fix=nmea.quality == 1,
                    lat=nmea.lat if nmea.lat != '' else 0,
                    lon=nmea.lon if nmea.lon != '' else 0,
                    hdop=nmea.HDOP if nmea.HDOP != '' else 0,
                    timestamp_utc_ms=int(time.time() * 1000)
                )
                with self._last_position_lock:
                    self._current_position = new_position

        except subprocess.SubprocessError as e:
            raise CommandGpsError(f"Subprocess error: {e}")
        
    def _log_multiline_output(self, lines: List[bytes], prefix: str, log_level: int) -> None:
        for line in lines:
            logger.log(log_level, f'{prefix}: {line.decode().strip()}')

    @property
    def position(self) -> Optional[GpsPosition]:
        with self._last_position_lock:
            return self._current_position
        
    @property
    def is_alive(self) -> bool:
        return self._read_thread.is_alive()

    def close(self):
        self._stop_event.set()
        self._read_thread.join(timeout=2)
        if self._read_thread.is_alive():
            raise CommandGpsError('Could not stop reader thread.')