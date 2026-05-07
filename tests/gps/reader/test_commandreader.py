import time

from positionsource.gps.reader.commandreader import CommandGpsReader


def test_read_single_message():
    reader = CommandGpsReader(command=['bash', '-c', 'while true; do echo -ne \'$GPGGA,102400.00,5224.103474,N,01044.997812,E,1,08,0.9,103.0,M,46.0,M,,*63\n\'; sleep 0.5; done'])
    time.sleep(1)  # Give the reader thread some time to read the message
    position = reader.position
    
    assert position is not None
    assert position.fix == True
    assert abs(position.lat - 52.4017246) < 1e-6
    assert abs(position.lon - 10.7499635) < 1e-6
    assert position.hdop == 0.9
    
    reader.close()

def test_read_duplicate_message():
    reader = CommandGpsReader(command=['bash', '-c', 'while true; do echo -ne \'$GPGGA,102400.00,5224.103474,N,01044.997812,E,1,08,0.9,103.0,M,46.0,M,,*63\n\'; sleep 0.5; done'])
    time.sleep(1)  # Give the reader thread some time to read the message
    position = reader.position
    time.sleep(1)  # Wait for the same message to be read again
    position2 = reader.position

    assert position == position2  # Position should not change due to duplicate message
    
    assert position is not None
    assert position.fix == True
    assert abs(position.lat - 52.4017246) < 1e-6
    assert abs(position.lon - 10.7499635) < 1e-6
    assert position.hdop == 0.9
    
    reader.close()