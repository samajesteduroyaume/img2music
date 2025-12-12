"""
Img2Music - AI Music Composer
Streamlit Version
"""
import streamlit as st
import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv
import time
import numpy as np
from PIL import Image
from google.api_core.exceptions import NotFound

# Import app modules
from jsonschema import validate, ValidationError
from cache import CompositionCache
from metrics import metrics, logger, log_user_action, track_time

# Safe import for audio_effects
AudioEffects = None
audio_effects_error = None
try:
    from audio_effects import AudioEffects
except Exception as e:
    audio_effects_error = str(e)
    st.error(f"❌ Erreur critique: audio_effects n'a pas pu être chargé: {e}")

# Safe import for music_utils
music_utils = None
music_utils_error = None
try:
    import music_utils
except Exception as e:
    music_utils_error = str(e)
    st.error(f"❌ Erreur critique: music_utils n'a pas pu être chargé: {e}")

# Load environment variables
load_dotenv()

# Server configuration
import socket

# Get the hostname and IP address
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

# Set the server configuration
st.set_page_config(
    page_title="Img2Music AI Composer",
    page_icon="🎼",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Affichage de la configuration actuelle
st.write("""
### Configuration de l'application
L'application est prête à l'emploi.
""")

# Initialize cache and effects
if 'composition_cache' not in st.session_state:
    st.session_state.composition_cache = CompositionCache(max_size=100, ttl_seconds=3600)
if 'audio_effects' not in st.session_state and AudioEffects is not None:
    st.session_state.audio_effects = AudioEffects(sample_rate=44100)
elif AudioEffects is None:
    st.warning("⚠️ Audio effects non disponibles. La composition utilisera l'audio brut.")

# Gemini Configuration
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_ID = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")

if not API_KEY:
    st.error("❌ Clé API Gemini non configurée. Veuillez configurer la variable d'environnement GEMINI_API_KEY (local: .env, Streamlit Cloud: secrets/env vars).")
else:
    genai.configure(api_key=API_KEY)

# JSON Schema for validation
def _get_music_schema():
    """Returns the JSON schema for music composition validation."""
    return {
        "type": "object",
        "required": ["mood", "tempo", "key", "time_signature", "reasoning", "tracks"],
        "properties": {
            "mood": {"type": "string"},
            "reasoning": {"type": "string"},
            "key": {"type": "string"},
            "time_signature": {"type": "string"},
            "tempo": {"type": "number", "minimum": 40, "maximum": 240},
            "suggested_instrument": {"type": "string"},
            "tracks": {
                "type": "object",
                "properties": {
                    "melody": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["note", "duration"],
                            "properties": {
                                "note": {"type": "string"},
                                "duration": {"type": "number", "minimum": 0.125, "maximum": 8.0}
                            }
                        }
                    },
                    "bass": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["note", "duration"],
                            "properties": {
                                "note": {"type": "string"},
                                "duration": {"type": "number", "minimum": 0.125, "maximum": 8.0}
                            }
                        }
                    },
                    "chords": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["notes", "duration"],
                            "properties": {
                                "notes": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "duration": {"type": "number", "minimum": 0.125, "maximum": 8.0}
                            }
                        }
                    }
                }
            }
        }
    }

# --- AI LOGIC ---
@st.cache_data(show_spinner=False)
def analyze_with_gemini(_image, audio_path=None):
    """Analyze image with Gemini AI to generate music composition."""
    if not API_KEY:
        logger.warning("API key not configured")
        return None, "⚠️ Configurez GEMINI_API_KEY."
    
    start_time = time.time()
    
    prompt = """
    Act as a professional music composer.
    Analyze the image (and audio if provided) to detect the exact emotion, atmosphere, and rhythmic feel.
    Compose a unique musical piece (approx 15-20s) that perfectly matches this analysis.
    
    1. Determine the Mood (e.g., "Melancholic Solitude", "Energetic Joy", "Dark Mystery").
    2. Select the best Musical Key (e.g., "C Minor", "F# Major", "D Dorian").
    3. Select a Time Signature (e.g., "4/4", "3/4", "6/8").
    4. Provide a brief "Reasoning" explaining why this music fits the image.
    
    You MUST output valid JSON following this EXACT structure:
    {
      "mood": "Ethereal Calm",
      "reasoning": "The soft pastel colors and misty landscape suggest a slow, dreamlike quality, best expressed in a major key with a flowing 3/4 rhythm.",
      "key": "Eb Major",
      "time_signature": "3/4",
      "tempo": 85,
      "suggested_instrument": "piano",
      "tracks": {
        "melody": [
          {"note": "Eb4", "duration": 1.0},
          {"note": "G4", "duration": 1.0},
          {"note": "Bb4", "duration": 1.0}
        ],
        "bass": [
          {"note": "Eb2", "duration": 3.0}
        ],
        "chords": [
          {"notes": ["Eb3", "G3", "Bb3"], "duration": 3.0}
        ]
      }
    }
    
    Rules:
    - Notes format: "C#4", "Bb3". Use "REST" for silence.
    - Duration is in beats (0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0).
    - Ensure melody, bass, and chords line up rhythmically (total duration matches).
    - Melody should be catchy and expressive.
    """
    
    try:
        model = genai.GenerativeModel(MODEL_ID)
        content = [prompt, _image]
        if audio_path:
            audio_file = genai.upload_file(path=audio_path)
            content.append(audio_file)
        
        response = model.generate_content(
            content,
            request_options={"timeout": 30}
        )
        
        # Extract JSON from response
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            parsed_json = json.loads(match.group(0))
            
            # Validate JSON schema
            try:
                validate(instance=parsed_json, schema=_get_music_schema())
                
                duration = time.time() - start_time
                metrics.record_api_call(duration, cached=False)
                log_user_action("composition_generated", {"tempo": parsed_json.get("tempo"), "mood": parsed_json.get("mood")})
                
                return parsed_json, "✅ Composition IA générée avec succès."
            except ValidationError as ve:
                logger.error(f"JSON validation error: {ve}")
                metrics.record_error("validation", str(ve))
                return None, f"❌ Erreur validation JSON: {ve.message}"
        
        return None, "❌ Erreur format JSON Gemini"
    except NotFound as e:
        logger.error(f"Model not found: {e}")
        metrics.record_error("api_model_not_found", str(e))
        return None, (
            "❌ Erreur API Gemini: le modèle configuré n'est pas disponible. "
            f"Modèle actuel: '{MODEL_ID}'.\n"
            "Veuillez ouvrir Google AI Studio, vérifier un modèle compatible avec generateContent, "
            "puis définir la variable d'environnement GEMINI_MODEL en conséquence."
        )
    except Exception as e:
        logger.exception("API call failed")
        metrics.record_error("api", str(e))
        return None, f"❌ Erreur API: {e}"

def process_composition(image, audio_file, instrument, use_reverb, use_delay, use_compression):
    """Process image and generate music composition."""
    if music_utils is None:
        st.error(f"❌ Erreur: music_utils n'est pas disponible. {music_utils_error}")
        return None
    
    start_time = time.time()
    
    with st.spinner("🎨 Analyse de l'image avec l'IA..."):
        analysis, msg = analyze_with_gemini(image, audio_file)
    
    if not analysis:
        # Check for critical errors (API Key issues)
        if "403" in msg or "API Key" in msg or "leaked" in msg:
            st.error(f"🛑 **Arrêt Critique**: {msg}")
            st.info("Veuillez mettre à jour votre clé API dans les secrets ou le fichier .env.")
            return None
            
        st.warning(f"⚠️ {msg}. Utilisation d'une composition de secours.")
        analysis = {
            "mood": "Fallback Basic",
            "tempo": 120,
            "tracks": {
                "melody": [{"note": "C4", "duration": 1}, {"note": "E4", "duration": 1}, {"note": "G4", "duration": 2}],
                "bass": [{"note": "C2", "duration": 4}],
                "chords": [{"notes": ["C3", "E3", "G3"], "duration": 4}]
            }
        }
    else:
        st.success(msg)
    
    inst = instrument if instrument != "Auto-Detect" else analysis.get('suggested_instrument', 'piano')
    
    with st.spinner("🎼 Génération de la partition..."):
        score = music_utils.json_to_music21(analysis)
        abc_content = music_utils.music21_to_abc(score)
    
    with st.spinner("🎵 Synthèse audio..."):
        wav_data = music_utils.score_to_audio(score, inst)

        # Apply effects if available
        if 'audio_effects' in st.session_state and st.session_state.audio_effects is not None:
            sr, audio_array = wav_data
            audio_float = audio_array.astype(np.float32) / 32767.0

            processed_audio = st.session_state.audio_effects.apply_effects_chain(
                audio_float,
                use_reverb=use_reverb,
                use_delay=use_delay,
                use_compression=use_compression,
                room_size=0.6,
                delay_time=0.25,
                feedback=0.35,
                delay_mix=0.25
            )

            processed_audio_int16 = (processed_audio * 32767).astype(np.int16)
            wav_data = (sr, processed_audio_int16)
        else:
            st.info("ℹ️ Effets audio non appliqués (module manquant)")
    
    with st.spinner("💾 Export MIDI et MP3..."):
        midi_path = music_utils.score_to_midi(score)
        mp3_path = music_utils.save_audio_to_mp3(wav_data[0], wav_data[1])
    
    metrics.record_composition(time.time() - start_time)
    
    return {
        'audio': wav_data,
        'abc': abc_content,
        'midi': midi_path,
        'mp3': mp3_path,
        'json': analysis
    }

def update_from_abc(abc_content, instrument, use_reverb, use_delay, use_compression):
    """Update audio from modified ABC notation."""
    if music_utils is None or not abc_content:
        return None
    
    with st.spinner("🔄 Mise à jour de la partition..."):
        score = music_utils.abc_to_music21(abc_content)
        if not score:
            st.error("❌ Erreur: Code ABC invalide")
            return None
        
        inst = instrument if instrument != "Auto-Detect" else 'piano'
        
        wav_data = music_utils.score_to_audio(score, inst)

        if 'audio_effects' in st.session_state and st.session_state.audio_effects is not None:
            sr, audio_array = wav_data
            audio_float = audio_array.astype(np.float32) / 32767.0

            processed_audio = st.session_state.audio_effects.apply_effects_chain(
                audio_float,
                use_reverb=use_reverb,
                use_delay=use_delay,
                use_compression=use_compression,
                room_size=0.6,
                delay_time=0.25,
                feedback=0.35,
                delay_mix=0.25
            )

            processed_audio_int16 = (processed_audio * 32767).astype(np.int16)
            wav_data = (sr, processed_audio_int16)
        
        midi_path = music_utils.score_to_midi(score)
        mp3_path = music_utils.save_audio_to_mp3(wav_data[0], wav_data[1])
    
    return {
        'audio': wav_data,
        'midi': midi_path,
        'mp3': mp3_path
    }

# --- STREAMLIT UI ---

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🎼 Img2Music: AI Composer</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">L\'IA analyse votre image et compose une partition musicale unique</p>', unsafe_allow_html=True)

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    instrument = st.selectbox(
        "🎹 Instrument Principal",
        ["Auto-Detect", "piano", "synth_retro", "strings", "bass", "guitar", "brass", "drums"],
        help="Choisissez l'instrument ou laissez l'IA décider"
    )
    
    st.subheader("🎚️ Effets Audio")
    use_reverb = st.checkbox("🌊 Reverb", value=False, help="Ajoute de la profondeur et de l'espace")
    use_delay = st.checkbox("🔁 Delay", value=False, help="Écho rythmique")
    use_compression = st.checkbox("📊 Compression", value=True, help="Égalise les dynamiques (recommandé)")
    
    st.divider()
    
    # Metrics
    if st.button("📊 Actualiser Métriques"):
        stats = metrics.get_stats()
        st.metric("Compositions", stats['total_compositions'])
        st.metric("Appels API", stats['api_calls'])
        st.metric("Taux de cache", stats['cache_hit_rate'])

# Main content
tab1, tab2, tab3 = st.tabs(["🎨 Composer", "📝 Éditeur ABC", "ℹ️ Aide"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 Entrées")
        uploaded_image = st.file_uploader(
            "Image Inspiratrice",
            type=["png", "jpg", "jpeg", "webp"],
            help="Uploadez une image qui vous inspire"
        )
        
        uploaded_audio = st.file_uploader(
            "Inspiration Audio (Optionnel)",
            type=["mp3", "wav", "ogg"],
            help="Optionnel: ajoutez un fichier audio pour influencer le rythme"
        )
        
        if uploaded_image:
            st.image(uploaded_image, caption="Image uploadée", width='stretch')
        
        compose_button = st.button("✨ COMPOSER LA PARTITION IA", type="primary", width='stretch')
    
    with col2:
        st.subheader("🎵 Résultats")
        
        if compose_button and uploaded_image:
            # Process composition
            image = Image.open(uploaded_image)
            audio_path = uploaded_audio.name if uploaded_audio else None
            
            result = process_composition(image, audio_path, instrument, use_reverb, use_delay, use_compression)
            
            if result:
                # Store in session state
                st.session_state.composition = result
                st.session_state.abc_content = result['abc']
        
            # Display results if available
        if 'composition' in st.session_state and st.session_state.composition:
            result = st.session_state.composition
            analysis = result.get('json', {})
            
            # --- AI Insights Display ---
            with st.expander("🧠 Analyse de l'IA (Détails)", expanded=True):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Emotion", analysis.get('mood', 'N/A'))
                c2.metric("Tonalité", analysis.get('key', 'C Major'))
                c3.metric("Tempo", f"{analysis.get('tempo', 120)} BPM")
                c4.metric("Signature", analysis.get('time_signature', '4/4'))
                
                if 'reasoning' in analysis:
                    st.info(f"💡 **Raisonnement de l'IA:** {analysis['reasoning']}")
            
            # Audio player
            try:
                audio_data = result['audio'][1]
                sample_rate = result['audio'][0]
                
                # Safety check: Ensure standard shape (samples, channels)
                if isinstance(audio_data, np.ndarray):
                    # If data looks like (channels, samples) e.g. (2, 44100), transpose it
                    if len(audio_data.shape) == 2 and audio_data.shape[0] < audio_data.shape[1]:
                        audio_data = audio_data.T
                
                st.audio(audio_data, format='audio/wav', sample_rate=sample_rate)
            except Exception as e:
                st.error(f"Erreur lors de la lecture audio: {e}")
                if isinstance(result['audio'][1], np.ndarray):
                     st.caption(f"Debug: Shape={result['audio'][1].shape}, Dtype={result['audio'][1].dtype}")
            
            # Download buttons
            col_midi, col_mp3 = st.columns(2)
            with col_midi:
                midi_path = result.get('midi')
                if midi_path and os.path.isfile(midi_path):
                    with open(midi_path, 'rb') as f:
                        st.download_button(
                            "📥 Télécharger MIDI",
                            f.read(),
                            file_name="composition.mid",
                            mime="audio/midi",
                            width='stretch'
                        )
                else:
                    st.error("❌ Erreur: Export MIDI échoué")
            with col_mp3:
                mp3_path = result.get('mp3')
                if mp3_path and mp3_path != "None" and os.path.isfile(mp3_path):
                    try:
                        with open(mp3_path, 'rb') as f:
                            st.download_button(
                                "📥 Télécharger MP3",
                                f.read(),
                                file_name="composition.mp3",
                                mime="audio/mpeg",
                                width='stretch'
                            )
                    except Exception as e:
                        st.error(f"❌ Erreur lors de l'ouverture du fichier MP3: {e}")
                else:
                    st.warning("⚠️ Export MP3 non disponible (ffmpeg requis)")
            
            # JSON Debug
            with st.expander("🔍 Détails JSON (Debug)"):
                st.json(result['json'])

with tab2:
    st.subheader("📝 Éditeur de Partition (Format ABC)")
    
    if 'abc_content' in st.session_state:
        abc_editor = st.text_area(
            "Code ABC (Modifiable)",
            value=st.session_state.abc_content,
            height=300,
            help="Modifiez le code ABC pour personnaliser la partition"
        )
        
        if st.button("🔄 Mettre à jour Audio & Partition", width='stretch'):
            updated = update_from_abc(abc_editor, instrument, use_reverb, use_delay, use_compression)
            if updated:
                st.session_state.composition.update(updated)
                st.session_state.abc_content = abc_editor
                st.success("✅ Partition mise à jour!")
                st.rerun()
        
        # Partition visuelle
        st.subheader("👁️ Partition Visuelle")
        st.components.v1.html(f"""
        <script src="https://cdnjs.cloudflare.com/ajax/libs/abcjs/6.2.2/abcjs-basic-min.js"></script>
        <div id="paper" style="background: white; padding: 20px; border-radius: 8px;"></div>
        <script>
            ABCJS.renderAbc('paper', `{abc_editor}`, {{ responsive: 'resize' }});
        </script>
        """, height=400)
    else:
        st.info("ℹ️ Composez d'abord une partition dans l'onglet 'Composer'")

with tab3:
    st.markdown("""
    ## 🎼 Guide d'Utilisation
    
    ### 1. Composer une Musique
    1. **Uploadez une image** qui vous inspire
    2. (Optionnel) Ajoutez un **fichier audio** pour influencer le rythme
    3. Choisissez un **instrument** ou laissez l'IA décider
    4. Activez les **effets audio** souhaités
    5. Cliquez sur **COMPOSER LA PARTITION IA**
    
    ### 2. Éditer la Partition
    - Allez dans l'onglet **Éditeur ABC**
    - Modifiez le code **ABC** 
    - Cliquez sur **Mettre à jour** pour régénérer l'audio
    - La partition visuelle se met à jour automatiquement
    
    ### 3. Instruments Disponibles
    - 🎹 **Piano**: Son riche avec harmoniques
    - 🎛️ **Synth Retro**: Onde carrée vintage
    - 🎻 **Strings**: Cordes avec vibrato naturel
    - 🎸 **Bass**: Basse profonde avec sub-octave
    - 🎸 **Guitar**: Guitare acoustique
    - 🎺 **Brass**: Cuivres avec harmoniques impaires
    - 🥁 **Drums**: Percussion/kick drum
    
    ### 4. Effets Audio
    - 🌊 **Reverb**: Ajoute de la profondeur et de l'espace
    - 🔁 **Delay**: Écho rythmique
    - 📊 **Compression**: Égalise les dynamiques (recommandé)
    
    ### 5. Export
    - **MIDI**: Pour édition dans votre DAW
    - **MP3**: Pour partage et écoute
    
    ### 💡 Astuces
    - Le **cache** accélère les requêtes identiques
    - Consultez les **métriques** dans la sidebar
    - Expérimentez avec différents instruments et effets !
    """)

# Footer
st.divider()
st.markdown(
    '<p style="text-align: center; color: #999;">Powered by Gemini AI & Streamlit | Version Streamlit 1.0</p>',
    unsafe_allow_html=True
)
