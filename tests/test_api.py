import pytest
from triangulator.core.triangulator import app  # ← Import depuis le fichier triangulator.py à la racine


@pytest.fixture
def client():
    """Fixture Flask pour simuler des requêtes HTTP."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_triangulate_missing_pointsetid(client):
    """Erreur si pointSetId absent dans le JSON."""
    response = client.post('/triangulate', json={})
    assert response.status_code == 400


def test_triangulate_invalid_json(client):
    """Erreur si le corps de la requête n'est pas du JSON valide."""
    response = client.post('/triangulate', data="ceci n'est pas du json", content_type='application/json')
    assert response.status_code == 400


def test_triangulate_valid_id_but_not_implemented(client):
    """
    Le pointSetId est fourni → la requête est valide,
    mais la triangulation n'est pas implémentée → erreur 500.
    """
    response = client.post('/triangulate', json={'pointSetId': '123'})
    assert response.status_code == 500  # NotImplementedError → Flask renvoie 500


def test_triangulate_rejects_non_post(client):
    """La route ne doit accepter que les requêtes POST."""
    response = client.get('/triangulate')
    assert response.status_code == 405  # Méthode non autorisée