---
title: Img2Music AI Composer
emoji: 🎼
colorFrom: indigo
colorTo: pink
sdk: gradio
sdk_version: 5.9.1
app_file: app.py
pinned: false
license: mit
short_description: Generate music scores from images via Gemini AI.
---

# 🎼 Img2Music: AI Composer

Transformez vos images en véritables compositions musicales (Mélodie, Accords, Basse) grâce à Google Gemini 1.5 Flash.

## ✨ Fonctionnalités

### 🎨 Composition IA
- **Analyse IA Visuelle** : Détecte l'humeur, le tempo et le style à partir d'images
- **Composition Note-par-Note** : L'IA écrit la partition complète (mélodie, basse, accords)
- **Support Audio** : Ajoutez un fichier audio pour influencer la composition

### 🎹 Synthèse Audio Améliorée
- **4 Instruments** : Piano, Synthé Rétro, Cordes, Basse
- **Qualité Professionnelle** : Enveloppes ADSR, vibrato, harmoniques riches
- **Export Multi-Format** : MIDI, MP3, WAV

### ⚡ Performance
- **Cache Intelligent** : Réduit les appels API et améliore la vitesse
- **Validation Robuste** : Schéma JSON strict pour éviter les erreurs
- **Timeout Configuré** : Pas de blocage de l'interface

### 🎼 Édition Interactive
- **Éditeur ABC** : Modifiez la partition en temps réel
- **Visualisation** : Partition affichée avec ABCJS
- **Régénération** : Mettez à jour l'audio après édition

## 🚀 Configuration

### Sur Hugging Face Spaces

1. Ajoutez votre clé API dans **Settings** > **Repository secrets**
   - Nom : `GEMINI_API_KEY`
   - Valeur : Votre clé API Gemini ([obtenir une clé](https://makersuite.google.com))

2. Le Space redémarrera automatiquement

### Développement Local

```bash
# Cloner le dépôt
git clone https://huggingface.co/spaces/Samajesteduroyaume/img2music
cd img2music

# Installer les dépendances
pip install -r requirements.txt

# Configurer la clé API
echo "GEMINI_API_KEY=votre_cle_ici" > .env

# Lancer l'application
python app.py
```

## 📚 Documentation

- [HUGGINGFACE_SECRETS.md](HUGGINGFACE_SECRETS.md) - Configuration des secrets
- [TESTING.md](TESTING.md) - Guide des tests automatisés

## 🧪 Tests

```bash
# Exécuter tous les tests
python3 test_suite.py

# Tests avec verbosité
python3 test_suite.py -v
```

## 🎯 Améliorations Récentes

- ✅ Cache intelligent avec LRU
- ✅ Validation JSON robuste
- ✅ Timeout API (30s)
- ✅ Qualité audio améliorée
- ✅ Suite de tests automatisés
- ✅ Versions épinglées

## 📝 Licence

MIT License - Voir le fichier LICENSE pour plus de détails.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

