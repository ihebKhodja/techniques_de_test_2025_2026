import pytest
from triangulator.triangulator import triangulate


class TestTriangulate:
    """Tests de l'algorithme de triangulation en éventail"""

    def test_triangulate_fewer_than_3_points(self):
        """0, 1 ou 2 points → aucun triangle"""
        assert triangulate([]) == []
        assert triangulate([(0, 0)]) == []
        assert triangulate([(0, 0), (1, 0)]) == []

    def test_triangulate_three_non_collinear_points(self):
        """3 points non colinéaires → 1 triangle"""
        points = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
        result = triangulate(points)
        assert len(result) == 1
        assert result[0] == (0, 1, 2)

    def test_triangulate_many_points_returns_n_minus_2_triangles(self):
        """N points non colinéaires → N-2 triangles"""
        import math
        points = [
            (math.cos(2 * math.pi * i / 20), math.sin(2 * math.pi * i / 20))
            for i in range(20)
        ]
        result = triangulate(points)
        assert len(result) == 18  # 20 - 2

    def test_triangulate_collinear_points_returns_empty(self):
        """Points colinéaires (3 ou plus) → aucun triangle"""
        assert triangulate([(i, 0.0) for i in range(10)]) == []
        assert triangulate([(0.0, i) for i in range(5)]) == []
        assert triangulate([(i, i) for i in range(3)]) == []

    def test_triangulate_almost_collinear_returns_one_triangle(self):
        """Points presque colinéaires → 1 triangle (seuil numérique)"""
        points = [(0.0, 0.0), (1.0, 0.0), (0.5, 1e-8)]
        result = triangulate(points)
        assert len(result) == 1