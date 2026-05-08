import time

from positionsource.gps.reader.commandreader import CommandGpsReader


def test_read_single_message():
    reader = CommandGpsReader(
        command=['bash', '-c', 'while true; do echo -ne \'$GPGGA,102400.00,5224.103474,N,01044.997812,E,1,08,0.9,103.0,M,46.0,M,,*63\n\'; sleep 0.5; done'],
        read_timeout_s=1
    )

    position = reader.position

    assert position is not None
    assert position.fix == True
    assert abs(position.lat - 52.4017246) < 1e-6
    assert abs(position.lon - 10.7499635) < 1e-6
    assert position.hdop == 0.9
    
    reader.close()

def test_read_duplicate_message():
    reader = CommandGpsReader(
        command=['bash', '-c', 'while true; do echo -ne \'$GPGGA,102400.00,5224.103474,N,01044.997812,E,1,08,0.9,103.0,M,46.0,M,,*63\n\'; sleep 0.5; done'],
        read_timeout_s=1
    )

    # Read two messages, the second one will be None because the the timeout will expire
    position = reader.position
    position2 = reader.position
    
    assert position is not None
    assert position.fix == True
    assert abs(position.lat - 52.4017246) < 1e-6
    assert abs(position.lon - 10.7499635) < 1e-6
    assert position.hdop == 0.9

    assert position2 is None
    
    reader.close()

def test_read_logfile():
    reader = CommandGpsReader(
        command=['bash', '-c', 'while IFS= read -r line; do echo \"$line\" | cut -d\';\' -f2-; sleep 0.05; done < tests/test_data/nmea.log'],
        read_timeout_s=1
    )

    positions = []
    for _ in range(5):
        positions.append(reader.position)

    assert len(positions) == 5

    # Make sure all positions are valid
    for pos in positions:
        assert pos is not None
        assert pos.fix == True

    # Make sure all position readings are different
    assert len(set(positions)) == 5

    reader.close()

def test_timeout():
    reader = CommandGpsReader(
        command=['sleep', '1'],
        read_timeout_s=0.5
    )

    position = reader.position

    assert position is None
    
    reader.close()