# 🔐 Configuration des Secrets Hugging Face

## ⚠️ IMPORTANT: Sécurité de la Clé API

Votre clé API Gemini **NE DOIT JAMAIS** être committée dans le code source.

### Étapes pour Configurer les Secrets sur Hugging Face Spaces

1. **Accédez à votre Space**
   - Allez sur https://huggingface.co/spaces/Samajesteduroyaume/img2music

2. **Ouvrez les Paramètres**
   - Cliquez sur l'onglet **Settings** (⚙️)

3. **Ajoutez le Secret**
   - Descendez jusqu'à la section **Repository secrets**
   - Cliquez sur **New secret**
   - Nom: `GEMINI_API_KEY`
   - Valeur: Votre clé API Gemini (obtenez-en une nouvelle sur https://makersuite.google.com)
   - Cliquez sur **Add secret**

4. **Redémarrez le Space**
   - Le Space redémarrera automatiquement et chargera le secret

### ⚠️ Action Urgente Requise

La clé API actuellement dans votre fichier `.env` est **exposée publiquement**:
```
AIzaSyD4dCjOD4Bz6MNfJaWR89RLbkqwfemxRBU
```

**Vous devez:**
1. ✅ Révoquer cette clé immédiatement sur https://console.cloud.google.com/apis/credentials
2. ✅ Générer une nouvelle clé API
3. ✅ L'ajouter comme secret Hugging Face (voir ci-dessus)
4. ✅ Supprimer le fichier `.env` de votre dépôt Git

### Vérification

Le fichier `.env` est déjà dans `.gitignore`, mais s'il a été commité précédemment, vous devez:

```bash
# Supprimer du dépôt Git (mais garder localement)
git rm --cached .env

# Commit et push
git commit -m "Remove exposed API key from repository"
git push
```

### Comment l'Application Charge la Clé

Le code dans `app.py` charge automatiquement la clé depuis:
1. Les variables d'environnement (Hugging Face Secrets)
2. Ou le fichier `.env` (développement local uniquement)

```python
from dotenv import load_dotenv
load_dotenv()  # Charge .env si présent (local)
API_KEY = os.getenv("GEMINI_API_KEY")  # Charge depuis env (HF Spaces)
```

### Développement Local

Pour le développement local, créez un fichier `.env` (qui ne sera jamais commité):

```bash
# .env (local uniquement)
GEMINI_API_KEY=votre_nouvelle_cle_api_ici
```

Ce fichier est ignoré par Git grâce au `.gitignore`.
