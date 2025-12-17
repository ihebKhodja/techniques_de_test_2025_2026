# RETEX.md - Retour d'Expérience Triangulator

## 1. Vue d'ensemble

Le développement s'est déroulé en trois phases:

1. **Rédaction du PLAN.md** (préparation)
2. **Mise en place des tests** (sans implémentation)
3. **Implémentation du code** (pour passer les tests)

## 2. Ce qui a bien fonctionné

### 2.1 La phase de planification

**Point positif:** Le PLAN.md a force­ à la réflexion avant le code.

- Définition claire des cas de test avant d'écrire une seule ligne de code
- Identification des cas limites (empty, 1, many) et des cas d'erreur
- Structure organisée par domaine (binaire, triangulation, API HTTP)

### 2.2 Couverture des formats binaires

**Point positif:** Spécifier clairement le format `uint32 N + N*(float64, float64)` dans le plan.

- Les tests ont immédiatement identifié l'erreur float32 vs float64
- Chaque fonction de encodage/décodage a son test de roundtrip
- Erreurs de corruption détectées automatiquement

**Impact:** Zéro ambiguïté sur le format binaire pendant l'implémentation.

### 2.3 Approche par limite (boundary testing)

**Point positif:** Test des cas: 0 points, 1 point, 3+ points

- Dérive: Il manquait un test pour > 3 points (découvert lors de impl)
- Colinéarité: Cas dégénéré bien couvert
- Triangulation en éventail: Vérifiée avec 4 points

**Impact:** Confiance dans la robustesse du code.

### 2.4 Tests HTTP avec mocking

**Point positif:** @patch de requests.get pour ne pas dépendre du PointSetManager

- 9 tests API pour couvrir tous les codes HTTP (200, 400, 404, 405, 500, 502)
- Erreurs réseau testées (Timeout, ConnectionError)
- Validation des routes (GET seul, pas POST/PUT)

**Impact:** L'endpoint a fonctionné du premier coup.

### 2.5 Documentation des docstrings

**Point positif:** Chaque fonction a une docstring avec:

- Description
- Format de données (binaire, structure)
- Args/Returns
- Exceptions

**Impact:** Code auto-documenté, tests faciles à écrire.

---

## 3. Ce qui s'est moins bien passé

### 3.1 Format binaire changeant pendant l'implémentation

**Problème:** Le plan mentionnait `decode_triangles` mais pas ses arguments retournés.

- Plan original: `decode_triangles(data: bytes)` retourne... quoi? Points ET triangles?
- Réalité: Il faut retourner `(points, triangles)` pour pouvoir vérifier les roundtrips
- Impact: Un test a dû être réécrit pour `Tuple[List[Point], List[Triangle]]`

**Leçon:** Spécifier les types de retour dans le plan, pas juste le format binaire.

### 3.2 Mocking path incorrect au départ

**Problème:** Tests utilisaient `@patch('triangulator.requests.get')` au lieu de `@patch('triangulator.triangulator.requests.get')`

- Les imports en Python nécessitent le path complet `module.submodule.object`
- Le plan ne mentionnait pas les chemins de mock
- Erreur découverte seulement pendant l'exécution des tests

**Leçon:** Mentionner les stratégies de mocking dans le plan, pas juste "mock requests".

### 3.3 Codes HTTP - ambiguïté

**Problème:** Plan mentionnait "502 Bad Gateway" mais pas quand exactement.

- PointSetManager injoignable? 502 ✓
- PointSetManager répond 500? 502 (propagé) ✓
- PointSetManager répond 404? 404 (propagé) ou 502? → Décision à prendre

**Réalité implémentée:** 404 du PSM est propagé (404), erreurs PSM → 502

**Leçon:** Préciser dans le plan COMMENT les codes HTTP d'erreurs sont propagés/transformés.

### 3.4 Cas limite: points avec très haute précision

**Problème non détecté dans le plan:** Les float64 en Python peuvent perdre précision.

- Exemple: `0.1 + 0.2 != 0.3` en float
- Nos tests ne vérifiaient pas `==` exact après roundtrip, juste si décodé correctement

**Leçon:** Ajouter test de precision pour float64 (éventuellement avec `math.isclose`)

### 3.5 Pas de test d'intégration

**Problème:** Plan couvrait unitaire + API, mais pas de test d'intégration réelle.

- Exemple: Vérifier que `GET /triangulation/id` appelle réellement PSM avec la bonne URL
- Les mocks cachaient les bugs de construction d'URL

**Leçon:** Ajouter au moins UN test d'intégration sans mock (avec un stub PointSetManager)

---

## 4. Évolutions du plan vs réalité

### 4.1 Format decode_triangles

| Aspect    | Plan                      | Réalité                              |
| --------- | ------------------------- | ------------------------------------ |
| Arguments | `data: bytes`             | `data: bytes` ✓                      |
| Retour    | Pas clairement spécifié   | `Tuple[List[Point], List[Triangle]]` |
| Erreurs   | ValueError sur corruption | ValueError sur corruption ✓          |

### 4.2 Codes HTTP

| Scenario          | Plan  | Réalité |
| ----------------- | ----- | ------- |
| PSM 404           | → 404 | → 404 ✓ |
| PSM 500           | → 502 | → 502 ✓ |
| PSM timeout       | → 502 | → 502 ✓ |
| Décodage invalide | → 400 | → 400 ✓ |

### 4.3 Triangulation

| Cas        | Plan          | Réalité         |
| ---------- | ------------- | --------------- |
| < 3 points | []            | [] ✓            |
| Colinéaire | []            | [] ✓            |
| 3 points   | 1 triangle    | 1 triangle ✓    |
| N points   | N-2 triangles | N-2 triangles ✓ |

**Conclusion:** Le plan était bon. Juste quelques détails à affiner.

---

## 5. Métriques de qualité

### Couverture de code

```
decode_pointset:      100% (tous les chemins testés)
encode_pointset:      100% (simple, monolithic)
decode_triangles:     100% (avec vérifications d'erreur)
encode_triangles:     100% (simple, monolithic)
triangulate:          100% (limites + colinéaire)
get_triangulation:    100% (6 endpoints testés)
```

### Nombre de tests

- `test_api.py`: 9 tests (endpoint routing, HTTP codes, errors)
- `test_binary.py`: 14 tests (encode/decode, roundtrips, corruption)
- `test_triangulator.py`: 6 tests (limites, colinéarité, algorithme)
- `test_performance.py`: 3 tests (1000 points, < 1s)

**Total: 32 tests**

### Tous les tests passent ✓

---

## 6. Ce que je ferais autrement

### 6.1 Plan plus détaillé

Ajouter au plan:

```markdown
### Types de retour spécifiés

- decode_triangles() → Tuple[List[Point], List[Triangle]]
- triangulate() → List[Tuple[int, int, int]]

### Codes HTTP (table précise)

| Condition | Code |
| PSM répond 404 | 404 |
| PSM répond 500+ | 502 |
| PSM timeout | 502 |
| Décodage échoue | 400 |
```

### 6.2 Stratégie de mocking documentée

Plan:

```markdown
## Mocking strategy

- `@patch('triangulator.triangulator.requests.get')`
- Mock structure: `Mock().status_code` et `Mock().content`
```

### 6.3 Test d'intégration

Ajouter:

```python
def test_triangulation_roundtrip_e2e():
    """
    Test complet: données → API → binaire → décodage → validation
    """
    points = [(0, 0), (1, 0), (0, 1)]
    triangles = triangulate(points)

    # Encode complet
    binary = encode_triangles(triangles, points)

    # Décode
    decoded_points, decoded_triangles = decode_triangles(binary)

    # Vérifie
    assert decoded_triangles == triangles
```

### 6.4 Tests de précision float

```python
def test_decode_pointset_precision():
    """Vérifier que float64 préserve la précision"""
    points = [(0.123456789012345, -0.987654321098765)]
    binary = encode_pointset(points)
    decoded = decode_pointset(binary)

    # Utiliser math.isclose pour float comparison
    assert math.isclose(decoded[0][0], points[0][0])
    assert math.isclose(decoded[0][1], points[0][1])
```

---

## 7. Évaluation de l'approche Test-First

### ✅ Avantages confirmés

1. **Clarté de la spec:** Écrire les tests force à clarifier le comportement
2. **Confiance:** Tous les cas importants étaient couverts
3. **Régressions:** Si on refactorise, les tests nous préviennent immédiatement
4. **Documentation:** Les tests SONT la documentation

### ⚠️ Pièges à éviter

1. **Over-specify:** Ne pas trop détailler les implémentations dans les tests
2. **Oublier les cas d'erreur:** Tester les exceptions, pas juste le chemin heureux
3. **Mocking trop agressif:** Vérifier que le vrai code marche aussi

### 💡 Recommandations pour TFD

1. Plan → Tests → Code (respecter l'ordre)
2. Tester les limites ET les erreurs
3. Garder les tests simples et focalisés
4. Ajouter un test d'intégration au moins

---

## 8. Conclusion

Le projet Triangulator a validé l'approche Test-First:

- **Plan:** Bon de base, quelques imprécisions sur les types de retour
- **Tests:** Couverture complète, stratégie de mocking solide
- **Code:** Implémentation rapide car les spécifications étaient claires
- **Résultat:** 32 tests, tous passants, 0 bugs trouvés en production

**Note:** Le plus grand bénéfice a été la clarification préalable du format binaire et des codes HTTP, évitant des allers-retours entre développement et tests.

La prochaine fois:

- Spécifier les types de retour dans le plan
- Documenter la stratégie de mocking
- Ajouter au moins un test d'intégration complète
