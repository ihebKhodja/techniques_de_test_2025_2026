"""
Tests d'API HTTP pour le Triangulator

Couvre:
- Routage des endpoints
- Codes HTTP
- Intégration avec PointSetManager (mock)
- Gestion des erreurs HTTP et réseau
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
    # Erreurs réseau
    requests.Timeout(),
    requests.ConnectionError(),
    requests.RequestException(),
])
@patch('triangulator.triangulator.requests.get')
def test_get_triangulation_returns_502_on_psm_failure(mock_get, client, error):
    """Toute erreur PSM (HTTP 5xx ou réseau) → 502."""
    if isinstance(error, Mock):
        mock_get.return_value = error
    else:
        mock_get.side_effect = error
    response = client.get('/triangulation/123')
    assert response.status_code == 502


# ============================================================================
# 4. Vérification de l'appel au PSM
# ============================================================================

@patch('triangulator.triangulator.requests.get')
def test_get_triangulation_calls_psm_with_correct_url(mock_get, client):
    """L'URL appelée inclut l'ID et le chemin /binary."""
    mock_get.return_value = Mock(status_code=200, content=struct.pack('<I', 0))
    test_id = '123e4567-e89b-12d3-a456-426614174000'
    client.get(f'/triangulation/{test_id}')
    mock_get.assert_called_once()
    url = mock_get.call_args[0][0]
    assert test_id in url
    assert '/binary' in url
    assert 'pointsetmanager' in url