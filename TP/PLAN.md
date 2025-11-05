# PLAN.md — Plan de tests

> **Projet :** Triangulator (TP Techniques de Test 2025/2026)
>
> **Auteur :** Iheb KHODJA

---

## 1. Objectifs

Ce document décrit le plan de tests prévu pour valider la qualité, la correction fonctionnelle, la robustesse et les performances du composant **Triangulator**.

Les objectifs principaux sont :

* Vérifier la conformité fonctionnelle face aux spécifications (format binaire PointSet/Triangles, API OpenAPI `triangulator.yml`).
* Assurer la robustesse contre les entrées invalides / scénarios réseau (PointSetManager indisponible, données corrompues).
* Mesurer les performances de sérialisation/désérialisation et de l'algorithme de triangulation sur différentes tailles de jeux de points.
* Obtenir une couverture de tests élevée (objectif : ≥ 90%) tout en garantissant la pertinence des tests.

---

## 2. Périmètre des tests

* **Inclus :**

  * La logique de parsing/écriture des formats binaires `PointSet` et `Triangles`.
  * L'algorithme de triangulation (correctitude sur cas simples et complexes).
  * L'API HTTP exposée par le Triangulator (conformité OpenAPI, codes HTTP, headers, payload binaire).
  * L'intégration avec le PointSetManager via requêtes HTTP (mocks et tests d'intégration).
  * Tests de performance et benchmark (séparés des tests unitaires).

* **Exclus :**

  * Implémentation interne du PointSetManager et sa base de données (sera simulée/mocquée).

---

## 3. Stratégie de tests

1. **Test First / TDD** : rédiger les tests unitaires et d'API avant (ou en priorité) l'implémentation.
2. **Niveaux de tests :**

   * **Unitaires** : fonctions pures (parser binaire, writer, opérations géométriques, helpers).
   * **Intégration** : Triangulator complet démarré en tant que service (Flask) avec PointSetManager moqué (réponses HTTP simulées). Vérifier end-to-end.
   * **API / Contract** : tests de conformité à l'OpenAPI (contrats et schéma binaire intégrité).
   * **Performance** : benchmarks isolés (marquage pytest `@pytest.mark.perf`) pour sérialisation/désérialisation et triangulation sur tailles croissantes.
   * **Robustesse** : tests d'erreurs réseau, données corrompues, timeouts, réponses partielles.
3. **Données de test** : combinaison de fixtures statiques (cas déterministes) et générées aléatoirement (pour couvrir des configurations variées).
4. **Séparation Perf/Unit** : usage d'un marqueur `perf` pour pouvoir exclure facilement les tests lourds (`pytest -m "not perf"`).

---

## 4. Cas de tests (exemples clés)

> Les cas ci‑dessous doivent être traduits en tests pytest détaillés avec fixtures et assertions.

### 4.1 Tests unitaires — parsing & sérialisation

* Parser `PointSet` :

  * Fichier binaire valide → nombre de points correct, coordonnées attendues.
  * Taille annoncée incohérente (header indique N mais bytes manquants) → lève une erreur claire (ValueError / CustomParseError).
  * Points avec valeurs NaN / inf → comportement défini (rejet ou normalisation).
* Writer `PointSet` : round-trip `serialize(parse(bytes)) == bytes` pour plusieurs jeux.
* Parser `Triangles` : lecture des sommets + indices → indices hors bornes doivent lever une erreur.

### 4.2 Tests unitaires — algorithme de triangulation (petits cas déterministes)

* 3 points formant un triangle simple → retourne exactement 1 triangle avec les bons indices.
* 4 points formant un carré → triangulation retournant 2 triangles couvrant la surface sans recouvrement.
* Points collinéaires (N≥2) → résultat défini (0 triangle) ou gestion explicite.
* Points dupliqués → élimination/gestion sans crash.
* Cas de la « coquille d'escargot » (un ensemble en spirale simple) → triangulation finie et conforme aux propriétés (aucun triangle dégénéré).

### 4.3 Tests d'intégration & API

* Endpoint `POST /triangulate` (ou selon OpenAPI) :

  * Envoi d'un PointSetID valide → récupère PointSet depuis PointSetManager (mock), retourne Triangles au format binaire; vérifier headers `Content-Type` et code 200.
  * PointSetManager retourne 404 → Triangulator retourne 404 ou code d'erreur documenté.
  * PointSetManager timeout / 500 → Triangulator gère la défaillance avec code 502/504 selon la politique choisie.
  * Payload malformé → Triangulator retourne 400.

### 4.4 Tests de performance

* Mesurer temps (ms) et mémoire pour :

  * Sérialisation / désérialisation `PointSet` pour N = 1k, 10k, 100k points.
  * Triangulation pour N = 1k, 10k (et plus si faisable), exécuter plusieurs runs et prendre moyenne/écart-type.
* Définir des seuils indicatifs (ex : N=10k doit s'exécuter en < X secondes — à déterminer lors des premiers runs).

### 4.5 Tests de robustesse / fuzzing

* Alimentation aléatoire de bytes (courtes séquences) au parser — s'assurer qu'aucune exécution malicieuse ne provoque crash non contrôlé.
* Réponses HTTP tronquées / chunked du PointSetManager.

---

## 5. Données & Fixtures

* `tests/fixtures/pointsets/` : jeux de points JSON + fichiers binaires pré-générés :

  * `triangle.pset` (3 points), `square.pset` (4 points), `collinear.pset`, `duplicates.pset`, `spiral_small.pset`.
* Générateurs (factories) pour créer PointSet aléatoires contrôlés (seedable) utilisés en tests de robustesse et performances.
* Mocks HTTP : `requests_mock` ou `responses` (selon la stratégie) pour intercepter appels vers PointSetManager.

---

## 6. Organisation du projet et conventions de tests

Structure proposée :

```
project/
├── triangulator/           # code source
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── api/
│   ├── perf/
│   └── fixtures/
├── Makefile
├── requirements.txt
├── dev_requirements.txt
└── PLAN.md
```

Conventions :

* Tests nommés `test_*.py`.
* Markers pytest : `@pytest.mark.perf` pour perf tests et `@pytest.mark.integration` pour tests d'intégration.
* Fixtures réutilisables dans `tests/conftest.py` (ex : `client`, `mock_pointset_manager`, `small_pointset`).

---

## 7. Outils & commandes

* Lancement tests (tous) :

```bash
make test
# qui exécute : pytest -q
```

* Lancement tests unitaires seulement (exclut `perf`) :

```bash
make unit_test
# e.g. pytest -q -m "not perf"
```

* Lancement tests performance uniquement :

```bash
make perf_test
# e.g. pytest -q -m perf
```

* Couverture :

```bash
make coverage
# e.g. coverage run -m pytest && coverage html
```

* Lint & doc :

```bash
make lint    # ruff check
make doc     # pdoc3 --output-dir docs triangulator
```

---

## 8. Critères d'acceptation

Le travail sera considéré satisfaisant si :

* Les tests couvrent les fonctionnalités listées dans ce plan et sont pertinents (corrélés à la logique business).
* Tous les tests unitaires passent et le service Triangulator respecte le contrat API dans les tests d'intégration.
* Les tests de performance documentés montrent des temps mesurés et conclusions (moyenne/écart) ; les tests perf sont isolés et non exécutés par défaut.
* La qualité de code via `ruff check` est satisfaisante et la documentation générée avec `pdoc3` est disponible.

---

## 9. Planning de rendu (sprint court)

* **Fin de séance 1** : rendu `PLAN.md` (ce document) — *obligatoire*.
* **Séance 2** : tests unitaires pour le parser/serializer et premiers tests d'algorithme (cas simples).
* **Séance 3** : API + tests d'intégration, mocks du PointSetManager.
* **Séance 4** : tests de performance et rapport de couverture + documentation.

---

## 10. Annexes — Cas de tests concrets à implémenter en priorité

* `test_parse_pointset_roundtrip()` : round-trip pour petits jeux.
* `test_triangulate_triangle()` : 3 points -> 1 triangle, indices correspondants.
* `test_triangulate_square()` : 4 points -> 2 triangles couvrant le polygone.
* `test_collinear_points_no_triangle()` : colinéarité gérée.
* `test_api_triangulate_success()` : endpoint triangulate retourne `Content-Type: application/octet-stream` et binaire valide.
* `test_api_pointset_not_found()` : simuler 404 du PointSetManager.

---

### Remarques finales

Ce plan est volontairement pragmatique et priorise d'abord la **couverture fonctionnelle pertinente** avant d'atteindre une couverture quantitative maximale. On itérera sur les seuils de performance et sur la définition précise des codes d'erreur API au fur et à mesure de l'avancement.

---


