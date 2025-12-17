"""
Tests de validation du format binaire

Couvre:
- Parsing du format binaire PointSet
- Validation de l'intégrité des données
- Gestion des formats corrompus
- Edge cases (ensembles vides, données manquantes)
"""

import struct
import pytest
from unittest.mock import patch, Mock
from triangulator.triangulator import app


@pytest.fixture
def client():
    """Fixture Flask pour simuler des requêtes HTTP."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ============================================================================
# 1. Validation du format binaire
# ============================================================================

@patch('triangulator.triangulator.requests.get')
def test_binary_format_invalid_header_returns_400(mock_get, client):
    """Données binaires trop courtes pour contenir un header → 400."""
    mock_get.return_value = Mock(status_code=200, content=b'\x00\x00')
    response = client.get('/triangulation/123')
    assert response.status_code == 400


@patch('triangulator.triangulator.requests.get')
def test_binary_format_corrupted_point_count_returns_400(mock_get, client):
    """Nombre de points annoncé > données disponibles → 400."""
    corrupted = struct.pack('<I', 10) + struct.pack('<dd', 0.0, 0.0)
    mock_get.return_value = Mock(status_code=200, content=corrupted)
    response = client.get('/triangulation/123')
    assert response.status_code == 400


@patch('triangulator.triangulator.requests.get')
def test_binary_format_incomplete_point_data_returns_400(mock_get, client):
    """Point incomplet (seulement coordonnée x) → 400."""
    incomplete = struct.pack('<I', 1) + struct.pack('<d', 1.0)  # Manque y
    mock_get.return_value = Mock(status_code=200, content=incomplete)
    response = client.get('/triangulation/123')
    assert response.status_code == 400


# ============================================================================
# 2. Edge cases du format binaire
# ============================================================================

@patch('triangulator.triangulator.requests.get')
def test_binary_format_empty_pointset_is_valid(mock_get, client):
    """Un PointSet vide (0 points) est techniquement valide."""
    empty_pointset = struct.pack('<I', 0)
    mock_get.return_value = Mock(status_code=200, content=empty_pointset)
    response = client.get('/triangulation/123')
    assert response.status_code == 200


@patch('triangulator.triangulator.requests.get')
def test_binary_format_single_point_is_valid(mock_get, client):
    """Un seul point est valide (même si pas de triangulation possible)."""
    single_point = struct.pack('<I', 1) + struct.pack('<dd', 5.0, 10.0)
    mock_get.return_value = Mock(status_code=200, content=single_point)
    response = client.get('/triangulation/123')
    assert response.status_code == 200


@patch('triangulator.triangulator.requests.get')
def test_binary_format_two_points_is_valid(mock_get, client):
    """Deux points sont valides (pas de triangle mais format OK)."""
    two_points = struct.pack('<I', 2)
    two_points += struct.pack('<dd', 0.0, 0.0)
    two_points += struct.pack('<dd', 1.0, 1.0)
    mock_get.return_value = Mock(status_code=200, content=two_points)
    response = client.get('/triangulation/123')
    assert response.status_code == 200


# ============================================================================
# 3. Validation de l'endianness et types
# ============================================================================

@patch('triangulator.triangulator.requests.get')
def test_binary_format_uses_little_endian(mock_get, client):
    """Le format doit être little-endian (<)."""
    # Test avec 3 points en little-endian
    data = struct.pack('<I', 3)
    data += struct.pack('<dd', 0.0, 0.0)
    data += struct.pack('<dd', 1.0, 0.0)
    data += struct.pack('<dd', 0.0, 1.0)
    mock_get.return_value = Mock(status_code=200, content=data)
    response = client.get('/triangulation/123')
    assert response.status_code == 200


@patch('triangulator.triangulator.requests.get')
def test_binary_format_large_pointset(mock_get, client):
    """Teste un PointSet avec beaucoup de points."""
    num_points = 100
    data = struct.pack('<I', num_points)
    for i in range(num_points):
        data += struct.pack('<dd', float(i), float(i * 2))
    mock_get.return_value = Mock(status_code=200, content=data)
    response = client.get('/triangulation/123')
    assert response.status_code == 200


# ============================================================================
# 4. Validation des coordonnées spéciales
# ============================================================================

@pytest.mark.parametrize("x,y", [
    (0.0, 0.0),           # Origine
    (-100.0, -100.0),     # Coordonnées négatives
    (1e10, 1e10),         # Grandes valeurs
    (0.0000001, 0.0000001),  # Très petites valeurs
])
@patch('triangulator.triangulator.requests.get')
def test_binary_format_accepts_valid_coordinates(mock_get, client, x, y):
    """Diverses coordonnées valides doivent être acceptées."""
    data = struct.pack('<I', 1) + struct.pack('<dd', x, y)
    mock_get.return_value = Mock(status_code=200, content=data)
    response = client.get('/triangulation/123')
    assert response.status_code == 200


@patch('triangulator.triangulator.requests.get')
def test_binary_format_rejects_extra_bytes(mock_get, client):
    """Bytes supplémentaires après les données sont rejetés → 400."""
    data = struct.pack('<I', 1)
    data += struct.pack('<dd', 0.0, 0.0)
    data += b'\x00\x00\x00\x00'  # Garbage à la fin
    mock_get.return_value = Mock(status_code=200, content=data)
    response = client.get('/triangulation/123')
    assert response.status_code == 400