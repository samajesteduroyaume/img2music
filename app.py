import streamlit as st
import sys
import os

st.set_page_config(page_title="Debug Mode")

st.title("🛠️ Debug Application Img2Music")

st.write("✅ **Streamlit a démarré avec succès !**")

st.subheader("🔍 Informations Système")
st.code(f"Python: {sys.version}")
st.code(f"CWD: {os.getcwd()}")
st.code(f"Files: {os.listdir('.')}")

st.subheader("📦 Test des Imports")

modules_to_test = [
    "numpy",
    "PIL",
    "google.generativeai",
    "music21",
    "pydub",
    "jsonschema",
    "cache",
    "metrics", 
    "audio_effects",
    "music_utils"
]

for mod in modules_to_test:
    try:
        st.write(f"Importing `{mod}`...")
        __import__(mod)
        st.success(f"✅ `{mod}` importé avec succès")
    except Exception as e:
        st.error(f"❌ Echec import `{mod}`: {e}")
        st.exception(e)

st.success("Test terminé.")
