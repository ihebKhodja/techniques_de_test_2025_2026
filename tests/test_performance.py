
import pytest
import time
import struct
import random
from triangulator.triangulator import (
    decode_pointset,
    encode_pointset,
    triangulate,
    encode_triangles,
)


@pytest.mark.perf
class TestPerformance:
    """Tests de performance"""

    def test_decode_pointset_performance(self):
        """Décodage de 1000 points en < 1 seconde"""
        n = 1000
        random.seed(42)
        
        # Créer le binaire
        binary = struct.pack('<I', n)
        for _ in range(n):
            binary += struct.pack('<dd', 
                                  random.uniform(0, 100),
                                  random.uniform(0, 100))
        
        # Mesurer le temps
        start = time.perf_counter()
        points = decode_pointset(binary)
        elapsed = time.perf_counter() - start
        
        # Vérifications
        assert len(points) == n
        assert elapsed < 1.0, f"Décodage trop lent: {elapsed:.3f}s"

    def test_encode_pointset_performance(self):
        """Encodage de 1000 points en < 1 seconde"""
        n = 1000
        random.seed(42)
        
        points = [
            (random.uniform(0, 100), random.uniform(0, 100))
            for _ in range(n)
        ]
        
        start = time.perf_counter()
        binary = encode_pointset(points)
        elapsed = time.perf_counter() - start
        
        # Vérifications
        assert len(binary) == 4 + n * 16
        assert elapsed < 1.0, f"Encodage trop lent: {elapsed:.3f}s"

    def test_triangulate_performance(self):
        """Triangulation de 1000 points en < 1 seconde"""
        n = 1000
        random.seed(42)
        
        points = [
            (random.uniform(0, 100), random.uniform(0, 100))
            for _ in range(n)
        ]
        
        start = time.perf_counter()
        triangles = triangulate(points)
        elapsed = time.perf_counter() - start
        
        # Vérifications
        # Soit colinéaires (rare), soit N-2 triangles
        if triangles:
            assert len(triangles) == n - 2
        
        assert elapsed < 1.0, f"Triangulation trop lente: {elapsed:.3f}s"

    def test_encode_triangles_performance(self):
        """Encodage de triangles pour 1000 points en < 1 seconde"""
        n = 1000
        random.seed(42)
        
        points = [
            (random.uniform(0, 100), random.uniform(0, 100))
            for _ in range(n)
        ]
        
        # Créer des triangles (fan triangulation)
        triangles = [(i, i+1, i+2) for i in range(0, n-2)]
        
        start = time.perf_counter()
        binary = encode_triangles(triangles, points)
        elapsed = time.perf_counter() - start
        
        # Vérifications
        assert len(binary) > 0
        assert elapsed < 1.0, f"Encodage triangles trop lent: {elapsed:.3f}s"

    def test_roundtrip_performance(self):
        """Roundtrip complet (encode → decode) pour 1000 points"""
        n = 1000
        random.seed(42)
        
        points = [
            (random.uniform(0, 100), random.uniform(0, 100))
            for _ in range(n)
        ]
        
        start = time.perf_counter()
        
        # Encode
        binary = encode_pointset(points)
        
        # Decode
        decoded = decode_pointset(binary)
        
        elapsed = time.perf_counter() - start
        
        # Vérifications
        assert decoded == points
        assert elapsed < 1.0, f"Roundtrip trop lent: {elapsed:.3f}s"


@pytest.mark.perf
def test_end_to_end_performance():
    """Test E2E complet: 1000 points → triangulate → encode"""
    n = 1000
    random.seed(42)
    
    # Étape 1: Créer points
    points = [
        (random.uniform(0, 100), random.uniform(0, 100))
        for _ in range(n)
    ]
    
    start = time.perf_counter()
    
    # Étape 2: Encoder pointset
    pointset_binary = encode_pointset(points)
    
    # Étape 3: Décoder pointset
    decoded_points = decode_pointset(pointset_binary)
    
    # Étape 4: Triangulate
    triangles = triangulate(decoded_points)
    
    # Étape 5: Encoder triangles
    result_binary = encode_triangles(triangles, decoded_points)
    
    elapsed = time.perf_counter() - start
    
    # Vérifications
    assert len(result_binary) > 0
    assert elapsed < 2.0, f"E2E trop lent: {elapsed:.3f}s"