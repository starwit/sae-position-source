import time
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Optional

import serial
from pynmeagps import NMEAMessage, NMEAReader

from .datatypes import GpsPosition


class SerialGpsError(Exception):
    pass

class SerialGpsReader:
    '''This class reads GPS data from a serial device and provides the latest position. It uses a separate thread to read data continuously.
        It needs to be closed properly to release the serial port.'''
    def __init__(self, serial_device: Path):
        self._stop_event = Event()
        self._current_position: GpsPosition = None
        self._read_thread: Thread = Thread(target=self._gps_read_loop, kwargs={'serial_device': serial_device, 'stop_event': self._stop_event})
        self._last_position_lock = Lock()
        self._read_thread.start()

    def _gps_read_loop(self, serial_device: Path, stop_event: Event):
        '''This method runs in a separate thread. Do not call it directly.'''
        try:
            with serial.Serial(str(serial_device), baudrate=9600, timeout=1) as ser:
                while not stop_event.is_set():
                    line = ser.readline()
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

        except serial.SerialException as e:
            raise SerialGpsError(f"Serial error: {e}")

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
            raise SerialGpsError('Could not stop reader thread.')