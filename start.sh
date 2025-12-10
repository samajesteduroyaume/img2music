#!/bin/bash

# Arrêter tout processus Streamlit en cours
echo "Arrêt des processus Streamlit en cours..."
pkill -f "streamlit run"

# Attendre que les ports soient libérés
echo "Libération des ports..."
sleep 2

# Démarrer Streamlit avec les bonnes options
echo "Démarrage de l'application Streamlit..."
streamlit run app.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.enableCORS=false \
  --server.enableXsrfProtection=false

# En cas d'erreur
if [ $? -ne 0 ]; then
  echo "Erreur lors du démarrage de l'application"
  exit 1
fi
