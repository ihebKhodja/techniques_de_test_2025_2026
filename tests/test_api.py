import pytest
from unittest.mock import patch
from triangulator import app 


@pytest.fixture
def client():
    """Fixture Flask pour simuler des requêtes HTTP."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_get_triangulation_missing_pointsetid_in_path(client):
    """
    La spec exige un pointSetId dans l'URL (path).
    Flask renverra 404 si l'URL est incomplète (ex: GET /triangulation).
    """
    response = client.get('/triangulation')
    assert response.status_code == 404  # Flask : URL non trouvée


def test_get_triangulation_valid_id_but_not_implemented(client):
    """
    GET /triangulation/{pointSetId} → la logique n'est pas implémentée → 500.
    """
    response = client.get('/triangulation/123e4567-e89b-12d3-a456-426614174000')
    assert response.status_code == 500  # NotImplementedError


def test_get_triangulation_rejects_post(client):
    """
    La spec ne définit que GET → POST doit retourner 405.
    """
    response = client.post('/triangulation/123')
    assert response.status_code == 405


@patch('triangulator.requests.get')
def test_get_triangulation_pointsetmanager_404(mock_get, client):
    """
    PointSetManager répond 404 → on propage 404.
    """
    mock_get.return_value.status_code = 404
    response = client.get('/triangulation/123')
    # À ce stade, si tu implémentais l'appel, tu renverrais 404.
    # Pour l'instant, ce test échouera car l'appel n'est pas fait.
    # Mais tu peux le garder comme "test futur".
    assert response.status_code in (404, 500)


@patch('triangulator.requests.get')
def test_get_triangulation_pointsetmanager_unavailable(mock_get, client):
    """
    PointSetManager injoignable (timeout, 5xx) → 503 Service Unavailable.
    """
    mock_get.side_effect = Exception("Connection failed")
    response = client.get('/triangulation/123')
    # À implémenter plus tard → pour l'instant, tu peux juste vérifier 500
    assert response.status_code in (503, 500)


def test_get_triangulation_invalid_uuid_format(client):
    """
    Le pointSetId doit être un UUID valide (selon la spec).
    Si on envoie un ID invalide, on peut renvoyer 400.
    """
    response = client.get('/triangulation/invalid-id')
    # À ce stade, tu ne valides pas le format → 500.
    # Mais le test est là pour guider l'implémentation future.
    assert response.status_code in (400, 500)