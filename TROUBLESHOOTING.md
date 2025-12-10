# 🔧 Guide de Dépannage - Erreur Build Hugging Face

## 🚨 Problème Actuel

**Statut**: Build Error sur https://huggingface.co/spaces/Samajesteduroyaume/img2music  
**Erreur**: `Job failed with exit code: 1`  
**Logs détaillés**: Non accessibles (SSE désactivé)

---

## 🔍 Causes Probables

### 1. ⚠️ Imports Circulaires ou Manquants

**Symptôme**: L'application ne peut pas démarrer car un module ne peut pas être importé.

**Fichiers concernés**:
- `app.py` importe `cache`, `metrics`, `audio_effects`, `music_utils`
- `metrics.py` pourrait avoir des dépendances manquantes
- `audio_effects.py` utilise numpy

**Solution à tester**:
```python
# Vérifier que tous les imports sont présents
# Dans app.py (déjà fait):
import numpy as np  # ✅ Ajouté

# Vérifier music_utils.py
import numpy as np  # ✅ Présent
import tempfile     # ✅ Présent
```

### 2. 📦 Dépendances Incompatibles

**Symptôme**: Une dépendance ne peut pas être installée ou est incompatible.

**Problèmes potentiels**:
- `music21==9.1.0` pourrait nécessiter des dépendances système
- `pydub==0.25.1` nécessite `ffmpeg` (déjà dans `packages.txt`)
- Conflit de versions entre packages

**Solution à tester**:
```txt
# requirements.txt actuel
gradio==5.9.1
google-generativeai==0.8.3
numpy==2.3.5
pillow==10.2.0
python-dotenv==1.0.1
midiutil==1.2.1
pillow-heif==0.20.0
music21==9.1.0
pydub==0.25.1
jsonschema==4.23.0
requests==2.31.0
```

### 3. 🔑 Clé API Manquante

**Symptôme**: L'application démarre mais crash au premier appel API.

**Statut**: ⚠️ **PAS ENCORE CONFIGURÉE**

**Solution**:
1. Aller sur https://huggingface.co/spaces/Samajesteduroyaume/img2music/settings
2. Cliquer sur "Repository secrets"
3. Ajouter: `GEMINI_API_KEY` = votre clé API

### 4. 🐍 Version Python Incompatible

**Symptôme**: Syntaxe ou fonctionnalités non supportées.

**Solution**: Spécifier la version Python dans `README.md`:
```yaml
---
title: Img2Music AI Composer
sdk: gradio
sdk_version: 5.9.1
python_version: 3.10  # ← Ajouter cette ligne
app_file: app.py
---
```

---

## 🛠️ Solutions à Tester (Par Ordre de Priorité)

### Solution 1: Simplifier les Imports (Rapide)

Créer un fichier `app_simple.py` minimal pour tester:

```python
# app_simple.py
import gradio as gr
import os

def hello(name):
    return f"Hello {name}!"

demo = gr.Interface(fn=hello, inputs="text", outputs="text")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
```

**Test**: Si ça marche, le problème vient des imports complexes.

### Solution 2: Vérifier music21 (Moyen)

`music21` peut nécessiter des dépendances système supplémentaires.

**Créer un fichier `apt-packages.txt`** (au lieu de `packages.txt`):
```
ffmpeg
libsndfile1
```

### Solution 3: Désactiver Temporairement les Effets Audio (Moyen)

Commenter les effets audio pour isoler le problème:

```python
# Dans app.py, ligne ~228
# processed_audio = audio_effects.apply_effects_chain(...)
# Remplacer par:
processed_audio = audio_float  # Pas d'effets temporairement
```

### Solution 4: Utiliser des Versions Plus Anciennes (Lent)

Tester avec des versions plus stables:

```txt
# requirements.txt alternatif
gradio==4.44.0  # Version plus ancienne
google-generativeai==0.7.2
numpy==1.26.4
music21==9.0.0
```

---

## 📋 Plan d'Action Étape par Étape

### Étape 1: Diagnostic Local

```bash
# Dans le dossier img2music
cd /home/selim/Bureau/img2music

# Créer un environnement virtuel propre
python3 -m venv test_env
source test_env/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Tester l'import
python3 -c "import app"
```

**Si erreur**: Noter l'erreur exacte et la corriger.

### Étape 2: Spécifier la Version Python

Modifier `README.md`:

```yaml
---
title: Img2Music AI Composer
emoji: 🎼
colorFrom: indigo
colorTo: pink
sdk: gradio
sdk_version: 5.9.1
python_version: "3.10"  # ← AJOUTER
app_file: app.py
pinned: false
license: mit
---
```

### Étape 3: Créer un Fichier de Démarrage Robuste

Créer `startup.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Starting Img2Music..."
echo "Python version: $(python --version)"
echo "Installing dependencies..."

pip install -r requirements.txt

echo "✅ Dependencies installed"
echo "Starting Gradio app..."

python app.py
```

Modifier `README.md`:

```yaml
sdk: gradio
sdk_version: 5.9.1
app_file: startup.sh  # ← Au lieu de app.py
```

### Étape 4: Ajouter des Logs de Debug

Dans `app.py`, au début:

```python
import sys
print(f"🐍 Python version: {sys.version}", flush=True)
print(f"📦 Importing modules...", flush=True)

try:
    import gradio as gr
    print("✅ Gradio imported", flush=True)
except Exception as e:
    print(f"❌ Gradio import failed: {e}", flush=True)
    raise

# ... continuer pour chaque import
```

---

## 🎯 Solution Recommandée (Quick Fix)

**Créer une version minimale qui fonctionne, puis ajouter progressivement les fonctionnalités.**

### Fichier `app_minimal.py`:

```python
import gradio as gr
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

def simple_compose(image):
    if not API_KEY:
        return None, "⚠️ Configurez GEMINI_API_KEY dans les Secrets"
    
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content(["Décris cette image", image])
        return None, response.text
    except Exception as e:
        return None, f"Erreur: {e}"

with gr.Blocks() as demo:
    gr.Markdown("# 🎼 Img2Music - Version Minimale")
    
    with gr.Row():
        input_img = gr.Image(type="pil", label="Image")
        btn = gr.Button("Analyser")
    
    output = gr.Textbox(label="Résultat")
    
    btn.click(simple_compose, [input_img], [output])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
```

**Puis modifier `README.md`**:
```yaml
app_file: app_minimal.py  # Temporairement
```

**Une fois que ça marche**, réintégrer progressivement:
1. ✅ Version minimale
2. ➕ Ajouter `music_utils`
3. ➕ Ajouter `cache`
4. ➕ Ajouter `metrics`
5. ➕ Ajouter `audio_effects`

---

## 📞 Besoin d'Aide ?

**Pour obtenir les logs détaillés**:

1. **Via l'interface web** (si SSE activé):
   - https://huggingface.co/spaces/Samajesteduroyaume/img2music/logs

2. **Via l'API Hugging Face**:
   ```bash
   # Installer huggingface_hub
   pip install huggingface_hub
   
   # Se connecter
   huggingface-cli login
   
   # Récupérer les logs
   python -c "
   from huggingface_hub import HfApi
   api = HfApi()
   logs = api.get_space_runtime('Samajesteduroyaume/img2music')
   print(logs)
   "
   ```

3. **Contacter le support HF**:
   - https://huggingface.co/support

---

## ✅ Checklist de Vérification

Avant de redéployer:

- [ ] Tous les imports sont présents
- [ ] `requirements.txt` est correct
- [ ] `packages.txt` contient `ffmpeg`
- [ ] Version Python spécifiée dans `README.md`
- [ ] Clé API configurée dans les Secrets
- [ ] Test local réussi (`python app.py`)
- [ ] `.env` n'est PAS dans git
- [ ] Logs de debug ajoutés

---

## 🚀 Commandes de Déploiement

```bash
# 1. Tester localement
cd /home/selim/Bureau/img2music
python3 app.py

# 2. Commiter les changements
git add .
git commit -m "fix: Debug build error"

# 3. Pousser
git push origin main

# 4. Attendre 1-2 minutes
# 5. Vérifier sur HF
```

---

**Voulez-vous que j'applique une de ces solutions maintenant ?**
