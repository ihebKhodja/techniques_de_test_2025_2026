import pytest
from triangulator import triangulate

def test_triangulate_empty_input():
    """Triangulate with empty input should raise NotImplementedError (not implemented yet)."""
    with pytest.raises(NotImplementedError):
        triangulate([])

def test_triangulate_single_point():
    """Triangulate with one point should raise NotImplementedError."""
    with pytest.raises(NotImplementedError):
        triangulate([(1.0, 2.0)])

def test_triangulate_multiple_points():
    """Triangulate with multiple points should raise NotImplementedError."""
    with pytest.raises(NotImplementedError):
        triangulate([(0,0), (1,0), (0,1)])
