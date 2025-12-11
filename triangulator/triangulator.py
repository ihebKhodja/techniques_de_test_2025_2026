"""Triangulator Service.

Composant responsable de:
1. Récupérer les pointsets via le PointSetManager
2. Décoder/encoder les données binaires
3. Calculer les triangulations
4. Exposer l'API REST
"""

import struct

import requests
from flask import Flask, Response, jsonify

# Types
Point = tuple[float, float]
Triangle = tuple[int, int, int]

# Constants for binary format
BYTES_PER_POINT = 16  # 2 * float64 (8 bytes each)
BYTES_PER_TRIANGLE = 12  # 3 * uint32 (4 bytes each)
HEADER_SIZE = 4  # uint32

app = Flask(__name__)

# Configuration
POINTSET_MANAGER_URL = "http://pointsetmanager.local"
REQUEST_TIMEOUT = 5


# ============================================================================
# 1. DÉCODAGE/ENCODAGE BINAIRE - POINTSET
# ============================================================================


def decode_pointset(binary_data: bytes) -> list[Point]:
    """Décode un ensemble de points depuis un format binaire.

    Format attendu:
        uint32 N = nombre de points
        N * (float64 x, float64 y)

    Args:
        binary_data: bytes contenant les données encodées

    Returns:
        list[Point]: Liste de tuples (x, y) où x, y sont des float64

    Raises:
        ValueError: Si le format binaire est invalide ou corrompu

    """
    if len(binary_data) < HEADER_SIZE:
        raise ValueError(
            f"Binaire trop court: au minimum {HEADER_SIZE} bytes attendus "
            f"pour le header, reçu {len(binary_data)} bytes"
        )

    offset = 0

    # Lire le nombre de points
    try:
        (count,) = struct.unpack_from("<I", binary_data, offset)
    except struct.error as e:
        raise ValueError(f"Erreur lors de la lecture du nombre de points: {e}") from e

    offset += HEADER_SIZE
    expected_length = HEADER_SIZE + count * BYTES_PER_POINT
    if len(binary_data) != expected_length:
        raise ValueError(
            f"Longueur invalide: attendu {expected_length} bytes pour "
            f"{count} points, reçu {len(binary_data)} bytes"
        )

    # Décoder tous les points
    points = []
    for i in range(count):
        try:
            x, y = struct.unpack_from("<dd", binary_data, offset)
        except struct.error as e:
            raise ValueError(f"Erreur lors de la lecture du point {i}: {e}") from e
        offset += BYTES_PER_POINT
        points.append((x, y))

    return points


def encode_pointset(points: list[Point]) -> bytes:
    """Encode un ensemble de points au format binaire.

    Format:
        uint32 N = nombre de points
        N * (float64 x, float64 y)

    Args:
        points: Liste de tuples (x, y)

    Returns:
        bytes: Données encodées au format binaire

    Raises:
        ValueError: Si les points ne sont pas du format correct

    """
    try:
        out = [struct.pack("<I", len(points))]
        for x, y in points:
            out.append(struct.pack("<dd", float(x), float(y)))
        return b"".join(out)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Erreur lors de l'encodage des points: {e}") from e


# ============================================================================
# 2. DÉCODAGE/ENCODAGE BINAIRE - TRIANGLES
# ============================================================================


def decode_triangles(data: bytes) -> tuple[list[Point], list[Triangle]]:
    """Décode les points et triangles depuis un format binaire complet.

    Format:
        uint32 N (nombre de points)
        N * (float64 x, float64 y)
        uint32 T (nombre de triangles)
        T * (uint32 a, uint32 b, uint32 c)

    Args:
        data: bytes contenant les données encodées

    Returns:
        tuple[list[Point], list[Triangle]]: Points et triangles décodés

    Raises:
        ValueError: Si le format binaire est invalide ou corrompu

    """
    if len(data) < HEADER_SIZE:
        raise ValueError("Binaire trop court: au minimum 4 bytes attendus")

    offset = 0

    # Décoder les points
    try:
        (count,) = struct.unpack_from("<I", data, offset)
    except struct.error as e:
        raise ValueError(f"Erreur lors de la lecture du nombre de points: {e}") from e

    offset += HEADER_SIZE
    points = []
    for i in range(count):
        if offset + BYTES_PER_POINT > len(data):
            raise ValueError(
                f"Données corrompues: point {i} incomplet, "
                f"offset={offset}, len={len(data)}"
            )
        try:
            x, y = struct.unpack_from("<dd", data, offset)
        except struct.error as e:
            raise ValueError(f"Erreur lors de la lecture du point {i}: {e}") from e
        offset += BYTES_PER_POINT
        points.append((x, y))

    # Décoder les triangles
    if offset + HEADER_SIZE > len(data):
        raise ValueError("Données corrompues: nombre de triangles manquant")

    try:
        (tcount,) = struct.unpack_from("<I", data, offset)
    except struct.error as e:
        raise ValueError(
            f"Erreur lors de la lecture du nombre de triangles: {e}"
        ) from e
    offset += HEADER_SIZE
    triangles = []
    for i in range(tcount):
        if offset + BYTES_PER_TRIANGLE > len(data):
            raise ValueError(
                f"Données corrompues: triangle {i} incomplet, "
                f"offset={offset}, len={len(data)}"
            )
        try:
            a, b, c = struct.unpack_from("<III", data, offset)
        except struct.error as e:
            raise ValueError(f"Erreur lors de la lecture du triangle {i}: {e}") from e
        offset += BYTES_PER_TRIANGLE
        triangles.append((a, b, c))

    if offset != len(data):
        raise ValueError(
            f"Données excédentaires: {len(data) - offset} bytes non lus après "
            f"la fin des données attendues"
        )

    return points, triangles


def encode_triangles(triangles: list[Triangle], vertices: list[Point]) -> bytes:
    """Encode les points et triangles au format binaire complet.

    Format:
        uint32 N (nombre de points)
        N * (float64 x, float64 y)
        uint32 T (nombre de triangles)
        T * (uint32 i, uint32 j, uint32 k)

    Args:
        triangles: Liste de tuples (a, b, c) représentant les indices de points
        vertices: Liste de points (x, y)

    Returns:
        bytes: Données encodées au format binaire

    Raises:
        ValueError: Si les données ne sont pas du format correct

    """
    try:
        out = [struct.pack("<I", len(vertices))]
        for x, y in vertices:
            out.append(struct.pack("<dd", float(x), float(y)))
        out.append(struct.pack("<I", len(triangles)))
        for a, b, c in triangles:
            out.append(struct.pack("<III", int(a), int(b), int(c)))
        return b"".join(out)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Erreur lors de l'encodage des triangles: {e}") from e


# ============================================================================
# 3. TRIANGULATION
# ============================================================================


def triangulate(points: list[Point]) -> list[Triangle]:
    """Calculate fan triangulation from a list of points.

    Algorithme:
    - Si < 3 points: retourne liste vide
    - Si tous les points sont colinéaires: retourne liste vide
    - Sinon: crée une triangulation en éventail à partir du point 0

    La triangulation en éventail connecte le premier point à toutes les
    arêtes de la chaîne des autres points.

    Exemple avec 4 points [0, 1, 2, 3]:
        Triangles: (0,1,2), (0,2,3)

    Args:
        points: Liste de points à trianguler

    Returns:
        list[Triangle]: Liste de triangles (a, b, c) où a, b, c sont des indices

    Raises:
        ValueError: En cas d'erreur interne de calcul

    """
    n = len(points)
    if n < 3:
        return []

    def are_collinear(p1: Point, p2: Point, p3: Point) -> bool:
        """Vérifie si trois points sont colinéaires via le produit vectoriel."""
        cross_product = (
            (p2[0] - p1[0]) * (p3[1] - p1[1]) -
            (p2[1] - p1[1]) * (p3[0] - p1[0])
        )
        return abs(cross_product) < 1e-12

    all_collinear = True
    for i in range(2, n):
        if not are_collinear(points[0], points[1], points[i]):
            all_collinear = False
            break

    if all_collinear:
        return []

    return [(0, i, i + 1) for i in range(1, n - 1)]


# ============================================================================
# 4. ENDPOINT REST
# ============================================================================


@app.route("/triangulation/<pointSetId>", methods=["GET"])
def get_triangulation(pointSetId: str) -> Response:
    """Récupère la triangulation d'un PointSet.

    Endpoint: GET /triangulation/{pointSetId}

    Procédure:
    1. Appelle le PointSetManager pour obtenir le PointSet en binaire
    2. Décode les points
    3. Calcule la triangulation
    4. Encode et renvoie le résultat

    Args:
        pointSetId: UUID du PointSet (passé en route param)

    Returns:
        Response: Fichier binaire encodé avec status HTTP 200
                  ou erreur JSON avec status HTTP approprié

    Status codes:
        200: Succès, contient les triangles encodés
        400: Erreur de décodage/encodage des données
        404: PointSet introuvable (PointSetManager)
        405: Méthode HTTP non autorisée (Flask automatique)
        500: Erreur interne lors de la triangulation
        502: PointSetManager injoignable ou en erreur

    """
    try:
        url = f"{POINTSET_MANAGER_URL}/pointsets/{pointSetId}/binary"
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
    except requests.Timeout:
        return jsonify({
            "error": "PointSetManager timeout",
            "details": (
                f"Requête vers {POINTSET_MANAGER_URL} expirée après "
                f"{REQUEST_TIMEOUT}s"
            )
        }), 502
    except requests.ConnectionError as e:
        return jsonify({
            "error": "PointSetManager unreachable",
            "details": f"Impossible de se connecter à {POINTSET_MANAGER_URL}: {str(e)}"
        }), 502
    except requests.RequestException as e:
        return jsonify({
            "error": "PointSetManager request failed",
            "details": str(e)
        }), 502

    if response.status_code == 404:
        return jsonify({"error": "PointSet not found", "pointSetId": pointSetId}), 404

    if response.status_code != 200:
        return jsonify({
            "error": "PointSetManager error",
            "status_code": response.status_code
        }), 502

    try:
        points = decode_pointset(response.content)
    except ValueError as e:
        return jsonify({
            "error": "Invalid PointSet binary format",
            "details": str(e)
        }), 400
    except Exception as e:
        return jsonify({"error": "PointSet decode failed", "details": str(e)}), 400

    try:
        triangles = triangulate(points)
    except Exception as e:
        return jsonify({"error": "Triangulation failed", "details": str(e)}), 500

    try:
        result = encode_triangles(triangles, points)
    except ValueError as e:
        return jsonify({"error": "Triangle encoding failed", "details": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Encoding failed", "details": str(e)}), 500

    return Response(result, content_type="application/octet-stream")


# ============================================================================
# 5. AUTRES ENDPOINTS / INFO
# ============================================================================


@app.route("/health", methods=["GET"])
def health() -> Response:
    """Healthcheck endpoint."""
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)