import pytest
import struct
from triangulator import decode_pointset, encode_pointset, decode_triangles, encode_triangles


def test_decode_pointset_empty():
    with pytest.raises(NotImplementedError):
        decode_pointset(struct.pack('<L', 0))

def test_decode_pointset_single_point():
    with pytest.raises(NotImplementedError):
        decode_pointset(struct.pack('<Lff', 1, 1.5, -2.0))

def test_decode_pointset_multiple_points():
    binary = struct.pack('<L', 3)
    for x, y in [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]:
        binary += struct.pack('<ff', x, y)
    with pytest.raises(NotImplementedError):
        decode_pointset(binary)

def test_encode_pointset_empty():
    with pytest.raises(NotImplementedError):
        encode_pointset([])

def test_encode_pointset_roundtrip():
    with pytest.raises(NotImplementedError):
        original = [(1.0, 2.0), (3.0, 4.0)]
        encoded = encode_pointset(original)
        decode_pointset(encoded)

def test_decode_triangles_empty():
    binary = struct.pack('<L', 0) + struct.pack('<L', 0)
    with pytest.raises(NotImplementedError):
        decode_triangles(binary)

def test_decode_triangles_one_triangle():
    vertex_data = struct.pack('<L', 3)
    vertex_data += struct.pack('<ff', 0.0, 0.0)
    vertex_data += struct.pack('<ff', 1.0, 0.0)
    vertex_data += struct.pack('<ff', 0.0, 1.0)
    triangle_data = struct.pack('<L', 1) + struct.pack('<LLL', 0, 1, 2)
    with pytest.raises(NotImplementedError):
        decode_triangles(vertex_data + triangle_data)

def test_encode_triangles_roundtrip():
    with pytest.raises(NotImplementedError):
        vertices = [(0, 0), (1, 0)]
        triangles = [(0, 1, 0)]
        encoded = encode_triangles(triangles, vertices)
        decode_triangles(encoded)

def test_decode_pointset_corrupted_too_short():
    with pytest.raises(NotImplementedError):
        decode_pointset(struct.pack('<L', 2))

def test_decode_pointset_corrupted_wrong_size():
    with pytest.raises(NotImplementedError):
        decode_pointset(struct.pack('<L', 1) + struct.pack('<f', 1.0))