# PLAN.md — Plan de tests

> **Projet :** Triangulator (TP Techniques de Test 2025/2026)
>
> **Auteur :** Iheb KHODJA

---

## 1. Objectifs

Ce document décrit le plan de tests prévu pour valider la qualité, la correction fonctionnelle, la robustesse et les performances du composant **Triangulator**.

Les objectifs principaux sont :

- Vérifier la conformité fonctionnelle face aux spécifications (format binaire PointSet/Triangles, API OpenAPI `triangulator.yml`).
- Assurer la robustesse contre les entrées invalides / scénarios réseau (PointSetManager indisponible, données corrompues).
- Mesurer les performances de sérialisation/désérialisation et de l'algorithme de triangulation sur différentes tailles de jeux de points.
- Obtenir une couverture de tests élevée (objectif : ≥ 90%) tout en garantissant la pertinence des tests.

---

## 2. Périmètre des tests

- **Inclus :**

  - La logique de parsing/écriture des formats binaires `PointSet` et `Triangles`.
  - L'algorithme de triangulation (correctitude sur cas simples et complexes).
  - L'API HTTP exposée par le Triangulator (conformité OpenAPI, codes HTTP, headers, payload binaire).
  - L'intégration avec le PointSetManager via requêtes HTTP (mocks et tests d'intégration).
  - Tests de performance et benchmark (séparés des tests unitaires).

- **Exclus :**

  - Implémentation interne du PointSetManager et sa base de données (sera simulée/mocquée).

---

## 3. Stratégie de tests

1. **Test First / TDD** : rédiger les tests unitaires et d'API avant (ou en priorité) l'implémentation.
2. **Niveaux de tests :**

   - **Unitaires** : fonctions pures (parser binaire, writer, opérations géométriques, helpers).
   - **Intégration** : Triangulator complet démarré en tant que service (Flask) avec PointSetManager moqué (réponses HTTP simulées). Vérifier end-to-end.
   - **API / Contract** : tests de conformité à l'OpenAPI (contrats et schéma binaire intégrité).
   - **Performance** : benchmarks isolés (marquage pytest `@pytest.mark.perf`) pour sérialisation/désérialisation et triangulation sur tailles croissantes.
   - **Robustesse** : tests d'erreurs réseau, données corrompues, timeouts, réponses partielles.

3. **Données de test** : combinaison de fixtures statiques (cas déterministes) et générées aléatoirement (pour couvrir des configurations variées).
4. **Séparation Perf/Unit** : usage d'un marqueur `perf` pour pouvoir exclure facilement les tests lourds (`pytest -m "not perf"`).

---

## 4. Cas de tests (exemples clés)

> Les cas ci‑dessous doivent être traduits en tests pytest détaillés avec fixtures et assertions.

### 4.1 Tests unitaires — parsing & sérialisation

- Parser `PointSet` (`decode_pointset`):

  - Fichier binaire valide → nombre de points correct, coordonnées attendues
  - Taille annoncée incohérente → lève `ValueError` avec message explicite
  - Données tronquées → lève `ValueError`
  - Round-trip : `encode_pointset(decode_pointset(bytes)) == bytes` ✓

- Parser `Triangles` (`decode_triangles`):

  - Format binaire valide (points + triangles) → décode correctement
  - Données incomplètes → lève `ValueError`
  - Données excédentaires après fin attendue → lève `ValueError`
  - Indices hors bornes → **À valider** : acceptés ou rejetés ? (comportement non défini actuellement)

- Encoder `Triangles` (`encode_triangles`):

  - Round-trip : `decode_triangles(encode_triangles(...)) == ...` ✓
  - Entrées invalides (NaN, inf, types incorrects) → lève `ValueError`

### 4.2 Tests unitaires — algorithme de triangulation (petits cas déterministes)

- **Cas simples (3 points)** :

  - 3 points non colinéaires formant un triangle → retourne exactement 1 triangle `(0, 1, 2)`
  - Points colinéaires (3 ou plus) → retourne liste vide `[]`
  - Moins de 3 points (0, 1, 2) → retourne liste vide `[]`

- **Cas complexes (4+ points)** :

  - 4 points non colinéaires → triangulation en éventail retournant 2 triangles `(0,1,2), (0,2,3)`
  - 5+ points en cercle (non colinéaires) → N-2 triangles (propriété de tout fan triangulation)
  - Points presque colinéaires (seuil 1e-12) → comportement basé sur le produit vectoriel

- **Cas dégénérés** :
  - Points dupliqués → pas de gestion spéciale, traité comme des points distincts
  - Valeurs NaN / inf → pas de gestion spéciale, passent au travers (à tester)

### 4.3 Tests d'intégration & API

- Endpoint `GET /triangulation/<pointSetId>` :

  - Envoi d'une requête valide avec un PointSetID → récupère PointSet depuis PointSetManager (mock),
    retourne Triangles au format binaire; vérifier headers `Content-Type: application/octet-stream`
    et code 200.
  - PointSetManager retourne 404 → Triangulator retourne 404 avec message d'erreur.
  - PointSetManager timeout / 500 → Triangulator retourne 502 (Bad Gateway).
  - Données PointSet binaires malformées → Triangulator retourne 400.
  - Erreur lors de triangulation → Triangulator retourne 500.

### 4.4 Tests de performance

- Mesurer temps (ms) et mémoire pour :

  - Sérialisation / désérialisation `PointSet` pour N = 1k, 10k, 100k points.
  - Triangulation pour N = 1k, 10k (et plus si faisable), exécuter plusieurs runs et prendre moyenne/écart-type.

- Définir des seuils indicatifs (ex : N=10k doit s'exécuter en < X secondes — à déterminer lors des premiers runs).

### 4.5 Tests de robustesse / edge cases

- **Données binaires corrompues** :

  - Header incomplet (< 4 bytes) → ValueError
  - Nombre de points invalides → ValueError
  - Offset hors limites → ValueError

- **Intégration réseau** :

  - Timeout du PointSetManager → code 502
  - Réponse HTTP non 2xx → code 502 (sauf 404 → 404)
  - Données binaires tronquées de PointSetManager → code 400

- **Cas numériques** :
  - Points avec coordonnées très grandes (±1e308) → acceptés
  - Points avec coordonnées très petites (±1e-308) → acceptés
  - Seuil de colinéarité (1e-12) → testés explicitement

---

## 5. Données & Fixtures

- `tests/fixtures/pointsets/` : jeux de points JSON + fichiers binaires pré-générés :

  - `triangle.pset` (3 points), `square.pset` (4 points), `collinear.pset`, `duplicates.pset`, `spiral_small.pset`.

- Générateurs (factories) pour créer PointSet aléatoires contrôlés (seedable) utilisés en tests de robustesse et performances.
- Mocks HTTP : `requests_mock` ou `responses` (selon la stratégie) pour intercepter appels vers PointSetManager.

---

## 6. Organisation du projet et conventions de tests

Structure proposée :

```
project/
├── triangulator/
│ └── triangulator.py
├── tests/
│ ├── init.py
│ │── test_binary.py # parser/encoder
│ │── test_triangulation.py # algorithme triangulate()
│ │── test_api.py # endpoints REST
│ │── test_performance.py
├── Makefile
├── requirements.txt
├── dev_requirements.txt
└── PLAN.md
```

Conventions :

- Tests nommés `test_*.py`.
- Classes de tests groupant cas similaires : `class TestDecodePointSet`, `class TestTriangulate`.
- Markers pytest : `@pytest.mark.perf` pour perf tests et `@pytest.mark.integration`.
- Fixtures réutilisables dans `tests/conftest.py`.

---

## 7. Outils & commandes

- Lancement tests (tous) :

```bash
make test
# qui exécute : pytest -q
```

- Lancement tests unitaires seulement (exclut `perf`) :

```bash
make unit_test
# e.g. pytest -q -m "not perf"
```

- Lancement tests performance uniquement :

```bash
make perf_test
# e.g. pytest -q -m perf
```

- Couverture :

```bash
make coverage
# e.g. coverage run -m pytest && coverage html
```

- Lint & doc :

```bash
make lint    # ruff check
make doc     # pdoc3 --output-dir docs triangulator
```

---

## 8. Critères d'acceptation

Le travail sera considéré satisfaisant si :

- Les tests couvrent les fonctionnalités listées dans ce plan et sont pertinents (corrélés à la logique business).
- Tous les tests unitaires passent et le service Triangulator respecte le contrat API dans les tests d'intégration.
- Les tests de performance documentés montrent des temps mesurés et conclusions (moyenne/écart) ; les tests perf sont isolés et non exécutés par défaut.
- La qualité de code via `ruff check` est satisfaisante et la documentation générée avec `pdoc3` est disponible.

---

## 9. Planning de rendu (sprint court)

- **Fin de séance 1** : rendu `PLAN.md` (ce document) — _obligatoire_.
- **Séance 2** : tests unitaires pour le parser/serializer et premiers tests d'algorithme (cas simples).
- **Séance 3** : API + tests d'intégration, mocks du PointSetManager.
- **Séance 4** : tests de performance et rapport de couverture + documentation.

---

### 10. Annexes — Cas de tests concrets à implémenter en priorité

- `test_decode_encode_roundtrip()` : encode→decode retourne données identiques
- `test_triangulate_fewer_than_3_points()` : 0, 1, 2 points → []
- `test_triangulate_3_non_collinear()` : 3 points → 1 triangle (0,1,2)
- `test_triangulate_4_non_collinear()` : 4 points → 2 triangles (0,1,2), (0,2,3)
- `test_triangulate_collinear()` : N points colinéaires → []
- `test_decode_pointset_invalid_length()` : données tronquées → ValueError
- `test_api_get_triangulation_success()` : GET /triangulation/{id} → 200 + binaire valide
- `test_api_pointset_manager_404()` : PointSetManager 404 → Triangulator 404
- `test_api_pointset_manager_timeout()` : timeout → Triangulator 502

---

### Remarques finales

Ce plan est volontairement pragmatique et priorise d'abord la **couverture fonctionnelle pertinente** avant d'atteindre une couverture quantitative maximale. On itérera sur les seuils de performance et sur la définition précise des codes d'erreur API au fur et à mesure de l'avancement.

---
