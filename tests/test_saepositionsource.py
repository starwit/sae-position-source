import pytest
from pathlib import Path
from pynmeagps import NMEAReader, NMEAMessage

def gps_test_log():
    with open('tests/test_gps.log', 'r') as f:
        while len(line := f.readline()) > 0:
            timestamp, nmea_sentence = line.split(';')
            nmea: NMEAMessage = NMEAReader.parse(nmea_sentence)
            if nmea.msgID == 'GGA':
                yield nmea.lat, nmea.lon

def test_parser():
    for gps in gps_test_log():
        print(gps)