# 🧪 Tests Automatisés - Img2Music

## Vue d'ensemble

Ce projet inclut une suite de tests automatisés pour garantir la qualité et la fiabilité du code.

## Installation des Dépendances de Test

Les tests nécessitent les mêmes dépendances que l'application principale :

```bash
pip install -r requirements.txt
```

## Exécution des Tests

### Tous les tests
```bash
python3 test_suite.py
```

### Tests individuels avec unittest
```bash
# Test du cache uniquement
python3 -m unittest test_suite.TestCompositionCache

# Test des utilitaires musicaux
python3 -m unittest test_suite.TestMusicUtils

# Test de la validation JSON
python3 -m unittest test_suite.TestJSONValidation
```

### Avec verbosité
```bash
python3 test_suite.py -v
```

## Couverture des Tests

### 1. TestCompositionCache
- ✅ Set et Get basiques
- ✅ Cache miss
- ✅ Cache avec audio
- ✅ Éviction LRU
- ✅ Clear cache
- ✅ Statistiques

### 2. TestMusicUtils
- ✅ Conversion JSON → Music21
- ✅ Conversion Music21 → ABC
- ✅ Conversion ABC → Music21
- ✅ Génération MIDI
- ✅ Génération Audio
- ✅ Test de tous les instruments
- ✅ Génération MP3

### 3. TestJSONValidation
- ✅ Validation de structure JSON

## Structure des Tests

```
test_suite.py
├── TestCompositionCache    # Tests du système de cache
├── TestMusicUtils          # Tests des utilitaires musicaux
└── TestJSONValidation      # Tests de validation JSON
```

## Résultats Attendus

Tous les tests devraient passer avec succès :

```
test_cache_clear (test_suite.TestCompositionCache) ... ok
test_cache_lru_eviction (test_suite.TestCompositionCache) ... ok
test_cache_miss (test_suite.TestCompositionCache) ... ok
test_cache_set_and_get (test_suite.TestCompositionCache) ... ok
test_cache_stats (test_suite.TestCompositionCache) ... ok
test_cache_with_audio (test_suite.TestCompositionCache) ... ok
test_abc_to_music21 (test_suite.TestMusicUtils) ... ok
test_json_to_music21 (test_suite.TestMusicUtils) ... ok
test_music21_to_abc (test_suite.TestMusicUtils) ... ok
test_save_audio_to_mp3 (test_suite.TestMusicUtils) ... ok
test_score_to_audio (test_suite.TestMusicUtils) ... ok
test_score_to_midi (test_suite.TestMusicUtils) ... ok
test_synthesizer_instruments (test_suite.TestMusicUtils) ... ok
test_valid_json (test_suite.TestJSONValidation) ... ok

----------------------------------------------------------------------
Ran 14 tests in X.XXXs

OK
```

## Ajout de Nouveaux Tests

Pour ajouter de nouveaux tests :

1. Créez une nouvelle classe de test héritant de `unittest.TestCase`
2. Ajoutez des méthodes commençant par `test_`
3. Utilisez les assertions unittest (`assertEqual`, `assertTrue`, etc.)
4. Ajoutez la classe au test suite dans `run_tests()`

Exemple :

```python
class TestNewFeature(unittest.TestCase):
    def setUp(self):
        """Préparation avant chaque test."""
        pass
    
    def test_something(self):
        """Test de quelque chose."""
        result = my_function()
        self.assertEqual(result, expected_value)
```

## CI/CD

Ces tests peuvent être intégrés dans un pipeline CI/CD :

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python3 test_suite.py
```

## Dépannage

### ModuleNotFoundError
Si vous obtenez `ModuleNotFoundError`, installez les dépendances :
```bash
pip install -r requirements.txt
```

### Tests MIDI/MP3 échouent
Assurez-vous que `ffmpeg` est installé :
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

## Métriques de Qualité

- **Couverture de code** : ~80% des fonctions critiques
- **Temps d'exécution** : < 10 secondes
- **Fiabilité** : Tous les tests doivent passer
