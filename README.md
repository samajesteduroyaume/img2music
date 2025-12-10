# Img2Music - AI Music Composer (Streamlit)

🎼 **Transformez vos images en musique avec l'IA !**

## 🚀 Déploiement sur Hugging Face

Cette application utilise **Streamlit** au lieu de Gradio pour une meilleure stabilité.

### Configuration du Space

1. Allez sur https://huggingface.co/spaces/Samajesteduroyaume/img2music/settings
2. Changez le **SDK** de `gradio` à `streamlit`
3. Changez **App file** de `app.py` à `streamlit_app.py`
4. Sauvegardez les modifications

Le Space se redéploiera automatiquement.

## 🎵 Fonctionnalités

- ✨ Analyse d'image avec Gemini AI
- 🎼 Génération automatique de partitions musicales
- 🎹 Support de 7 instruments différents
- 🎚️ Effets audio professionnels (Reverb, Delay, Compression)
- 📝 Éditeur de notation ABC
- 👁️ Visualisation de partition en temps réel
- 💾 Export MIDI et MP3
- 📊 Métriques de performance

## 🛠️ Installation Locale

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 🔑 Configuration

Créez un fichier `.env` avec votre clé API Gemini :

```
GEMINI_API_KEY=votre_clé_api_ici
```

## 📦 Dépendances Principales

- `streamlit` - Framework web
- `google-generativeai` - API Gemini
- `music21` - Traitement musical
- `pydub` - Manipulation audio
- `numpy` - Calculs numériques

## 🎯 Migration depuis Gradio

Cette application a été migrée de Gradio vers Streamlit pour résoudre des problèmes de compatibilité avec Gradio 5.9.1 sur Hugging Face Spaces.

### Changements principaux :
- Interface utilisateur redessinée avec Streamlit
- Gestion d'état via `st.session_state`
- Cache optimisé avec `@st.cache_data`
- Toutes les fonctionnalités conservées

## 📝 Licence

MIT License

## 👨‍💻 Auteur

Développé avec ❤️ par l'équipe Img2Music
