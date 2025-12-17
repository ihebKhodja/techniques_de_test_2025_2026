"""
Tests d'API HTTP pour le Triangulator

Couvre:
- Routage des endpoints
- Codes HTTP
- Intégration avec PointSetManager (mock)
- Gestion des erreurs HTTP et réseau
- Tous les chemins d'exécution
"""

import struct
import pytest
import requests
from unittest.mock import patch, Mock
from triangulator.triangulator import app


@pytest.fixture
def client():
    """Fixture Flask pour simuler des requêtes HTTP."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ============================================================================
# 1. Tests de routage et méthodes HTTP
# ============================================================================

def test_get_triangulation_missing_pointsetid_in_path(client):
    """Flask renvoie 404 si l'URL ne contient pas de pointSetId."""
    response = client.get('/triangulation')
    assert response.status_code == 404


@pytest.mark.parametrize("method", ["post", "put", "delete", "patch"])
def test_rejects_non_get_methods(client, method):
    """Seule la méthode GET est autorisée sur /triangulation/<id>."""
    func = getattr(client, method)
    response = func('/triangulation/123e4567-e89b-12d3-a456-426614174000')
    assert response.status_code == 405


# ============================================================================
# 2. Test de succès
# ============================================================================

@patch('triangulator.triangulator.requests.get')
def test_get_triangulation_success(mock_get, client):
    """Cas normal : PSM 200 → endpoint 200 + binaire valide."""
    pointset_data = struct.pack('<I', 3)
    pointset_data += struct.pack('<dd', 0.0, 0.0)
    pointset_data += struct.pack('<dd', 1.0, 0.0)
    pointset_data += struct.pack('<dd', 0.0, 1.0)

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = pointset_data
    mock_get.return_value = mock_response

    response = client.get('/triangulation/123e4567-e89b-12d3-a456-426614174000')
    assert response.status_code == 200
    assert response.content_type == 'application/octet-stream'
    assert len(response.data) > 0


# ============================================================================
# 3. Tests erreurs PSM et réseau
# ============================================================================

@patch('triangulator.triangulator.requests.get')
def test_get_triangulation_propagates_psm_404(mock_get, client):
    """PSM 404 → endpoint 404."""
    mock_get.return_value = Mock(status_code=404)
    response = client.get('/triangulation/missing')
    assert response.status_code == 404


@pytest.mark.parametrize("error", [
    # Erreurs HTTP du PSM
    Mock(status_code=500),
    Mock(status_code=502),
    Mock(status_code=503),
])
@patch('triangulator.triangulator.requests.get')
def test_get_triangulation_returns_502_on_psm_http_failure(mock_get, client, error):
    """Toute erreur PSM (HTTP 5xx) → 502."""
    mock_get.return_value = error
    response = client.get('/triangulation/123')
    assert response.status_code == 502


@patch('triangulator.triangulator.requests.get')
def test_get_triangulation_returns_502_on_timeout(mock_get, client):
    """PSM timeout → 502"""
    mock_get.side_effect = requests.Timeout("Timeout occurred")
    response = client.get('/triangulation/123')
    assert response.status_code == 502
    assert b'PointSetManager timeout' in response.data


@patch('triangulator.triangulator.requests.get')
def test_get_triangulation_returns_502_on_connection_error(mock_get, client):
    """PSM ConnectionError → 502"""
    mock_get.side_effect = requests.ConnectionError("Connection failed")
    response = client.get('/triangulation/123')
    assert response.status_code == 502
    assert b'PointSetManager unreachable' in response.data


@patch('triangulator.triangulator.requests.get')
def test_get_triangulation_returns_502_on_request_exception(mock_get, client):
    """PSM RequestException → 502"""
    mock_get.side_effect = requests.RequestException("Generic error")
    response = client.get('/triangulation/123')
    assert response.status_code == 502
    assert b'PointSetManager request failed' in response.data


@patch('triangulator.triangulator.requests.get')
def test_get_triangulation_with_empty_pointset_returns_200(mock_get, client):
    """PointSet vide (0 points) → 200"""
    empty = struct.pack('<I', 0)
    mock_get.return_value = Mock(status_code=200, content=empty)
    response = client.get('/triangulation/123')
    assert response.status_code == 200
    assert len(response.data) > 0


@patch('triangulator.triangulator.requests.get')
def test_get_triangulation_with_two_points_returns_200(mock_get, client):
    """PointSet avec 2 points (pas de triangles possibles) → 200"""
    pointset_data = struct.pack('<I', 2)
    pointset_data += struct.pack('<dd', 0.0, 0.0)
    pointset_data += struct.pack('<dd', 1.0, 0.0)
    mock_get.return_value = Mock(status_code=200, content=pointset_data)
    response = client.get('/triangulation/123')
    assert response.status_code == 200
    assert len(response.data) > 0


# ============================================================================
# 4. Tests des chemins d'erreur de décodage
# ============================================================================

@patch('triangulator.triangulator.requests.get')
def test_get_triangulation_decode_error_returns_400(mock_get, client):
    """Erreur lors de decode_pointset (ValueError) → 400"""
    mock_get.return_value = Mock(status_code=200, content=b'SHORT')
    response = client.get('/triangulation/123')
    assert response.status_code == 400
    assert b'Invalid PointSet binary format' in response.data


@patch('triangulator.triangulator.requests.get')
def test_get_triangulation_decode_generic_exception_returns_400(mock_get, client):
    """Erreur générique lors de decode_pointset → 400"""
    mock_get.return_value = Mock(status_code=200, content=None)
    response = client.get('/triangulation/123')
    assert response.status_code == 400


# ============================================================================
# 5. Tests des chemins d'erreur de triangulation
# ============================================================================

@patch('triangulator.triangulator.requests.get')
@patch('triangulator.triangulator.triangulate')
def test_get_triangulation_triangulation_exception_returns_500(mock_triangulate, mock_get, client):
    """Exception lors de triangulate() → 500"""
    pointset_data = struct.pack('<I', 3)
    pointset_data += struct.pack('<dd', 0.0, 0.0)
    pointset_data += struct.pack('<dd', 1.0, 0.0)
    pointset_data += struct.pack('<dd', 0.0, 1.0)
    
    mock_get.return_value = Mock(status_code=200, content=pointset_data)
    mock_triangulate.side_effect = Exception("Triangulation error")
    
    response = client.get('/triangulation/123')
    assert response.status_code == 500
    assert b'Triangulation failed' in response.data


# ============================================================================
# 6. Tests des chemins d'erreur d'encodage
# ============================================================================

@patch('triangulator.triangulator.requests.get')
@patch('triangulator.triangulator.encode_triangles')
def test_get_triangulation_encode_valueerror_returns_400(mock_encode, mock_get, client):
    """ValueError lors de encode_triangles() → 400"""
    pointset_data = struct.pack('<I', 3)
    pointset_data += struct.pack('<dd', 0.0, 0.0)
    pointset_data += struct.pack('<dd', 1.0, 0.0)
    pointset_data += struct.pack('<dd', 0.0, 1.0)
    
    mock_get.return_value = Mock(status_code=200, content=pointset_data)
    mock_encode.side_effect = ValueError("Encoding error")
    
    response = client.get('/triangulation/123')
    assert response.status_code == 400
    assert b'Triangle encoding failed' in response.data


@patch('triangulator.triangulator.requests.get')
@patch('triangulator.triangulator.encode_triangles')
def test_get_triangulation_encode_generic_exception_returns_500(mock_encode, mock_get, client):
    """Exception générique lors de encode_triangles() → 500"""
    pointset_data = struct.pack('<I', 3)
    pointset_data += struct.pack('<dd', 0.0, 0.0)
    pointset_data += struct.pack('<dd', 1.0, 0.0)
    pointset_data += struct.pack('<dd', 0.0, 1.0)
    
    mock_get.return_value = Mock(status_code=200, content=pointset_data)
    mock_encode.side_effect = Exception("Generic encoding error")
    
    response = client.get('/triangulation/123')
    assert response.status_code == 500
    assert b'Encoding failed' in response.data


# ============================================================================
# 7. Test health endpoint
# ============================================================================

def test_health_endpoint(client):
    """Test health endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    assert b'ok' in response.data


# ============================================================================
# 8. Tests de validation des réponses binaires
# ============================================================================

@patch('triangulator.triangulator.requests.get')
def test_get_triangulation_returns_valid_binary_format(mock_get, client):
    """Réponse retourne un binaire valide et décodable"""
    pointset_data = struct.pack('<I', 4)
    pointset_data += struct.pack('<dd', 0.0, 0.0)
    pointset_data += struct.pack('<dd', 1.0, 0.0)
    pointset_data += struct.pack('<dd', 1.0, 1.0)
    pointset_data += struct.pack('<dd', 0.0, 1.0)
    
    mock_get.return_value = Mock(status_code=200, content=pointset_data)
    response = client.get('/triangulation/123')
    
    assert response.status_code == 200
    
    # Vérifier que le binaire retourné est valide
    from triangulator.triangulator import decode_triangles
    points, triangles = decode_triangles(response.data)
    assert len(points) == 4
    assert len(triangles) == 2  # 4 - 2 = 2 triangles


@patch('triangulator.triangulator.requests.get')
def test_get_triangulation_with_collinear_points_returns_200(mock_get, client):
    """Points colinéaires retournent 0 triangles mais 200"""
    pointset_data = struct.pack('<I', 3)
    pointset_data += struct.pack('<dd', 0.0, 0.0)
    pointset_data += struct.pack('<dd', 1.0, 0.0)
    pointset_data += struct.pack('<dd', 2.0, 0.0)
    
    mock_get.return_value = Mock(status_code=200, content=pointset_data)
    response = client.get('/triangulation/123')
    
    assert response.status_code == 200
    
    # Vérifier que 0 triangles sont retournés
    from triangulator.triangulator import decode_triangles
    points, triangles = decode_triangles(response.data)
    assert len(points) == 3
    assert len(triangles) == 0