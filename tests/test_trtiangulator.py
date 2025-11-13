# triangulator/tests/test_triangulator.py

import pytest
from triangulator.core.triangulate import triangulate

def test_triangulate_empty_input():
    """Test triangulate with empty input"""
    result = triangulate([])
    assert result is None  

def test_triangulate_single_point():
    """Test triangulate with one point"""
    result = triangulate([(1.0, 2.0)])
    assert result is None  

def test_triangulate_multiple_points():
    """Test triangulate with multiple points"""
    points = [(0,0), (1,0), (0,1)]
    result = triangulate(points)
    assert result is None  
