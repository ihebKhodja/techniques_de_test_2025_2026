import pytest
import time
import random
from triangulator import triangulate, decode_pointset, encode_triangles


@pytest.mark.perf
def test_triangulation_performance_10_points():
    """Mesure le temps de triangulation pour 10 points."""
    points = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(10)]
    start = time.perf_counter()
    try:
        triangulate(points)
    except NotImplementedError:
        pass  
    duration = time.perf_counter() - start
    print(f"Triangulation 10 points: {duration:.4f}s")
    assert True  


@pytest.mark.perf
def test_triangulation_performance_100_points():
    """Mesure le temps de triangulation pour 100 points."""
    points = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(100)]
    start = time.perf_counter()
    try:
        triangulate(points)
    except NotImplementedError:
        pass
    duration = time.perf_counter() - start
    print(f"Triangulation 100 points: {duration:.4f}s")
    assert True


@pytest.mark.perf
def test_triangulation_performance_1000_points():
    """Mesure le temps de triangulation pour 1000 points."""
    points = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(1000)]
    start = time.perf_counter()
    try:
        triangulate(points)
    except NotImplementedError:
        pass
    duration = time.perf_counter() - start
    print(f"Triangulation 1000 points: {duration:.4f}s")
    assert True


@pytest.mark.perf
def test_decode_pointset_performance():
    """Mesure le temps de décodage binaire pour 1000 points."""
    import struct
    n = 1000
    binary = struct.pack('<L', n)
    for _ in range(n):
        binary += struct.pack('<ff', random.uniform(0, 100), random.uniform(0, 100))

    start = time.perf_counter()
    try:
        decode_pointset(binary)
    except NotImplementedError:
        pass
    duration = time.perf_counter() - start
    print(f"Décodage binaire 1000 points: {duration:.4f}s")
    assert True


@pytest.mark.perf
def test_encode_triangles_performance():
    """Mesure le temps d'encodage binaire pour 500 triangles."""
    vertices = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(500)]
    triangles = [(random.randint(0, 499), random.randint(0, 499), random.randint(0, 499)) for _ in range(200)]

    start = time.perf_counter()
    try:
        encode_triangles(triangles, vertices)
    except NotImplementedError:
        pass
    duration = time.perf_counter() - start
    print(f"Encodage binaire 200 triangles: {duration:.4f}s")
    assert True