from flask import Flask
import requests

app = Flask(__name__)


def triangulate(points):
    raise NotImplementedError("Triangulation logic not implemented")

def decode_pointset(binary_data):
    raise NotImplementedError()

def encode_pointset(points):
    raise NotImplementedError()

def decode_triangles(data: bytes):
    raise NotImplementedError()

def encode_triangles(triangles, vertices):
    raise NotImplementedError()



@app.route('/triangulation/<pointSetId>', methods=['GET'])
def get_triangulation(pointSetId):
    """
    GET /triangulation/{pointSetId}
    Récupère le PointSet via le PointSetManager, calcule la triangulation,
    et renvoie les Triangles en binaire.
    """
    # À ce stade : pas d'implémentation → 500
    raise NotImplementedError("Triangulation endpoint not implemented")