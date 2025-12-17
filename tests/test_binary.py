"""
Tests de validation du format binaire

Couvre:
- Parsing du format binaire PointSet
- Validation de l'intégrité des données
- Gestion des formats corrompus
- Edge cases (ensembles vides, données manquantes)
- Tous les chemins de décodage/encodage
"""

import struct
import pytest
from unittest.mock import patch, Mock
from triangulator.triangulator import app, decode_pointset
from triangulator.triangulator import (
    encode_pointset, decode_triangles, encode_triangles
)


@pytest.fixture
def client():
    """Fixture Flask pour simuler des requêtes HTTP."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ============================================================================
# 1. TESTS DECODE_POINTSET - Direct (sans API)
# ============================================================================

def test_decode_pointset_empty():
    """decode_pointset avec 0 points"""
    data = struct.pack('<I', 0)
    result = decode_pointset(data)
    assert result == []


def test_decode_pointset_single_point():
    """decode_pointset avec 1 point"""
    data = struct.pack('<I', 1)
    data += struct.pack('<dd', 3.14, 2.71)
    result = decode_pointset(data)
    assert len(result) == 1
    assert result[0] == (3.14, 2.71)


def test_decode_pointset_multiple_points():
    """decode_pointset avec plusieurs points"""
    data = struct.pack('<I', 3)
    data += struct.pack('<dd', 0.0, 0.0)
    data += struct.pack('<dd', 1.0, 0.0)
    data += struct.pack('<dd', 0.0, 1.0)
    result = decode_pointset(data)
    assert len(result) == 3
    assert result == [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]


def test_decode_pointset_invalid_header_too_short():
    """decode_pointset avec header trop court"""
    data = b'\x00\x00'
    with pytest.raises(ValueError, match="trop court"):
        decode_pointset(data)


def test_decode_pointset_corrupted_length():
    """decode_pointset annonce plus de points que disponibles"""
    data = struct.pack('<I', 10)  # Annonce 10 points
    data += struct.pack('<dd', 0.0, 0.0)  # Mais n'en donne qu'1
    with pytest.raises(ValueError, match="Longueur invalide"):
        decode_pointset(data)


def test_decode_pointset_incomplete_point():
    """decode_pointset avec point incomplet"""
    data = struct.pack('<I', 1)  # 1 point annoncé
    data += struct.pack('<d', 1.0)  # Manque la coordonnée y
    with pytest.raises(ValueError, match="Longueur invalide"):
        decode_pointset(data)


# ============================================================================
# 2. TESTS ENCODE_POINTSET - Direct (sans API)
# ============================================================================

def test_encode_pointset_empty():
    """encode_pointset avec liste vide"""
    result = encode_pointset([])
    assert result == struct.pack('<I', 0)


def test_encode_pointset_single_point():
    """encode_pointset avec 1 point"""
    points = [(3.14, 2.71)]
    result = encode_pointset(points)
    assert len(result) == 4 + 16  # header + 1 point
    # Vérifier qu'on peut décoder
    decoded = decode_pointset(result)
    assert len(decoded) == 1


def test_encode_pointset_multiple_points():
    """encode_pointset avec plusieurs points"""
    points = [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)]
    result = encode_pointset(points)
    assert len(result) == 4 + 3*16  # header + 3 points
    decoded = decode_pointset(result)
    assert decoded == points


def test_encode_pointset_roundtrip():
    """encode → decode roundtrip"""
    original = [(1.5, 2.5), (-3.0, 4.5), (0.0, -1.0)]
    encoded = encode_pointset(original)
    decoded = decode_pointset(encoded)
    assert decoded == original


def test_encode_pointset_with_invalid_coordinates():
    """encode_pointset avec coordonnées invalides"""
    points = [(0.0, None)]
    with pytest.raises(ValueError):
        encode_pointset(points)


def test_encode_pointset_with_non_numeric():
    """encode_pointset avec strings"""
    points = [("a", "b")]
    with pytest.raises(ValueError):
        encode_pointset(points)


# ============================================================================
# 3. TESTS DECODE_TRIANGLES - Direct (sans API)
# ============================================================================

def test_decode_triangles_empty():
    """decode_triangles avec 0 points et 0 triangles"""
    data = struct.pack('<I', 0)  # 0 points
    data += struct.pack('<I', 0)  # 0 triangles
    points, triangles = decode_triangles(data)
    assert points == []
    assert triangles == []


def test_decode_triangles_valid_format():
    """decode_triangles avec format valide"""
    data = struct.pack('<I', 3)  # 3 points
    data += struct.pack('<dd', 0.0, 0.0)
    data += struct.pack('<dd', 1.0, 0.0)
    data += struct.pack('<dd', 0.0, 1.0)
    data += struct.pack('<I', 1)  # 1 triangle
    data += struct.pack('<III', 0, 1, 2)
    
    points, triangles = decode_triangles(data)
    assert len(points) == 3
    assert len(triangles) == 1
    assert triangles[0] == (0, 1, 2)


def test_decode_triangles_invalid_header():
    """decode_triangles avec header trop court"""
    data = b'\x00\x00'
    with pytest.raises(ValueError, match="trop court"):
        decode_triangles(data)


def test_decode_triangles_incomplete_point_data():
    """decode_triangles avec points incomplets"""
    data = struct.pack('<I', 100)  # Annonce 100 points
    data += struct.pack('<dd', 0.0, 0.0)  # Mais n'en donne qu'1
    with pytest.raises(ValueError, match="corrompues|incomplet"):
        decode_triangles(data)


def test_decode_triangles_incomplete_triangle_header():
    """decode_triangles avec header triangles manquant"""
    data = struct.pack('<I', 1)  # 1 point
    data += struct.pack('<dd', 0.0, 0.0)
    # Manque le header du nombre de triangles
    with pytest.raises(ValueError, match="manquant"):
        decode_triangles(data)


def test_decode_triangles_incomplete_triangle_data():
    """decode_triangles avec données triangles incomplètes"""
    data = struct.pack('<I', 1)  # 1 point
    data += struct.pack('<dd', 0.0, 0.0)
    data += struct.pack('<I', 1)  # 1 triangle annoncé
    data += struct.pack('<II', 0, 1)  # Mais seulement 2 indices au lieu de 3
    with pytest.raises(ValueError, match="incomplet"):
        decode_triangles(data)


def test_decode_triangles_extra_bytes():
    """decode_triangles avec bytes supplémentaires"""
    data = struct.pack('<I', 0)  # 0 points
    data += struct.pack('<I', 0)  # 0 triangles
    data += b'\xFF\xFF\xFF\xFF'  # Extra garbage
    with pytest.raises(ValueError, match="excédentaires"):
        decode_triangles(data)


# ============================================================================
# 4. TESTS ENCODE_TRIANGLES - Direct (sans API)
# ============================================================================

def test_encode_triangles_empty():
    """encode_triangles avec 0 points et 0 triangles"""
    points = []
    triangles = []
    result = encode_triangles(triangles, points)
    assert len(result) == 4 + 4  # 2 headers
    decoded_p, decoded_t = decode_triangles(result)
    assert decoded_p == []
    assert decoded_t == []


def test_encode_triangles_single_triangle():
    """encode_triangles avec 1 triangle"""
    points = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    triangles = [(0, 1, 2)]
    result = encode_triangles(triangles, points)
    assert len(result) == 4 + 3*16 + 4 + 1*12
    decoded_p, decoded_t = decode_triangles(result)
    assert decoded_p == points
    assert decoded_t == triangles


def test_encode_triangles_multiple_triangles():
    """encode_triangles avec plusieurs triangles"""
    points = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    triangles = [(0, 1, 2), (0, 2, 3)]
    result = encode_triangles(triangles, points)
    decoded_p, decoded_t = decode_triangles(result)
    assert decoded_p == points
    assert decoded_t == triangles


def test_encode_triangles_roundtrip():
    """encode → decode roundtrip avec triangles"""
    points = [(0.0, 0.0), (1.0, 0.0), (0.5, 1.0)]
    triangles = [(0, 1, 2)]
    encoded = encode_triangles(triangles, points)
    decoded_p, decoded_t = decode_triangles(encoded)
    assert decoded_p == points
    assert decoded_t == triangles


def test_encode_triangles_with_invalid_indices():
    """encode_triangles avec indices invalides"""
    points = [(0.0, 0.0), (1.0, 0.0)]
    triangles = [("a", "b", "c")]
    with pytest.raises(ValueError):
        encode_triangles(triangles, points)


def test_encode_triangles_with_invalid_vertices():
    """encode_triangles avec coordonnées invalides"""
    points = [(None, None), (1.0, 0.0)]
    triangles = [(0, 1, 0)]
    with pytest.raises(ValueError):
        encode_triangles(triangles, points)


# ============================================================================
# 5. TESTS VIA API FLASK
# ============================================================================

@patch('triangulator.triangulator.requests.get')
def test_api_binary_format_invalid_header_returns_400(mock_get, client):
    """API: données binaires trop courtes → 400"""
    mock_get.return_value = Mock(status_code=200, content=b'\x00\x00')
    response = client.get('/triangulation/123')
    assert response.status_code == 400


@patch('triangulator.triangulator.requests.get')
def test_api_binary_format_corrupted_point_count_returns_400(mock_get, client):
    """API: nombre de points > données disponibles → 400"""
    corrupted = struct.pack('<I', 10) + struct.pack('<dd', 0.0, 0.0)
    mock_get.return_value = Mock(status_code=200, content=corrupted)
    response = client.get('/triangulation/123')
    assert response.status_code == 400


@patch('triangulator.triangulator.requests.get')
def test_api_binary_format_empty_pointset(mock_get, client):
    """API: PointSet vide → 200"""
    empty = struct.pack('<I', 0)
    mock_get.return_value = Mock(status_code=200, content=empty)
    response = client.get('/triangulation/123')
    assert response.status_code == 200


@patch('triangulator.triangulator.requests.get')
def test_api_binary_format_single_point(mock_get, client):
    """API: PointSet avec 1 point → 200"""
    single = struct.pack('<I', 1) + struct.pack('<dd', 5.0, 10.0)
    mock_get.return_value = Mock(status_code=200, content=single)
    response = client.get('/triangulation/123')
    assert response.status_code == 200


@patch('triangulator.triangulator.requests.get')
def test_api_binary_format_rejects_extra_bytes(mock_get, client):
    """API: extra bytes après les données → 400"""
    data = struct.pack('<I', 1)
    data += struct.pack('<dd', 0.0, 0.0)
    data += b'\x00\x00\x00\x00'
    mock_get.return_value = Mock(status_code=200, content=data)
    response = client.get('/triangulation/123')
    assert response.status_code == 400