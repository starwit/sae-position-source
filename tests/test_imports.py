import pytest

def test_positionsource_import():
    try:
        from positionsource.saepositionsource import SaePositionSource
    except ImportError as e:
        pytest.fail(f"Failed to import GeoMapper: {e}")

    assert SaePositionSource is not None, "SaePositionSource should be imported successfully"
        
        