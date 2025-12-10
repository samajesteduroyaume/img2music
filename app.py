import sys
print("🚀 STARTUP IMPORTS: Gradio...", flush=True)
import gradio as gr
print(f"📦 Gradio Version: {gr.__version__} - FORCED REBUILD 17:05", flush=True)
print("🚀 STARTUP IMPORTS: Gemini...", flush=True)
import google.generativeai as genai
print("🚀 STARTUP IMPORTS: Standard libs...", flush=True)
import os
import json
import re
from dotenv import load_dotenv
try:
    print("🚀 STARTUP IMPORTS: Pillow-HEIF...", flush=True)
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    print("⚠️ STARTUP: Pillow-HEIF not found (OK)", flush=True)
    pillow_heif = None
print("🚀 STARTUP IMPORTS: App modules...", flush=True)
from jsonschema import validate, ValidationError
from cache import CompositionCache
print("🚀 STARTUP IMPORTS: Metrics...", flush=True)
from metrics import metrics, logger, log_user_action, track_time
print("🚀 STARTUP IMPORTS: Audio Effects...", flush=True)
from audio_effects import AudioEffects
import time
import numpy as np

# Safe import for music_utils (to prevent 500 Global Error if music21 fails)
music_utils = None
music_utils_error = None
try:
    import music_utils
except Exception as e:
    music_utils_error = str(e)
    print(f"CRITICAL ERROR IMPORTING MUSIC_UTILS: {e}")



# Charger les variables d'environnement
load_dotenv()

# Initialize cache and effects
composition_cache = CompositionCache(max_size=100, ttl_seconds=3600)
audio_effects = AudioEffects(sample_rate=44100)

logger.info("Img2Music application starting...")

# Configuration Gemini
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# JSON Schema for validation
MUSIC_JSON_SCHEMA = {
    "type": "object",
    "required": ["mood", "tempo", "tracks"],
    "properties": {
        "mood": {"type": "string"},
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

# --- LOGIQUE IA ---
@track_time("gemini_analysis")
def analyze_with_gemini(image, audio_path=None):
    if not API_KEY:
        logger.warning("API key not configured")
        return None, "⚠️ Configurez GEMINI_API_KEY."
    
    start_time = time.time()
    
    # Check cache first
    cached_composition = composition_cache.get(image, audio_path)
    if cached_composition:
        metrics.record_api_call(0, cached=True)
        log_user_action("composition_retrieved", {"source": "cache"})
        return cached_composition, "✨ Composition récupérée du cache (rapide!)."
    
    prompt = """
    Act as a professional music composer.
    Analyze the image (and audio if provided) and compose a unique short musical piece (approx 15-20s duration).
    If audio is provided, use its rhythm and mood to influence the composition.
    
    You MUST output valid JSON following this EXACT structure:
    {
      "mood": "Description of mood",
      "tempo": 100,
      "suggested_instrument": "piano",
      "tracks": {
        "melody": [
          {"note": "C4", "duration": 1.0},
          {"note": "E4", "duration": 0.5},
          {"note": "G4", "duration": 0.5},
          {"note": "REST", "duration": 1.0}
        ],
        "bass": [
          {"note": "C2", "duration": 2.0},
          {"note": "G2", "duration": 2.0}
        ],
        "chords": [
          {"notes": ["C3", "E3", "G3"], "duration": 4.0},
          {"notes": ["F3", "A3", "C4"], "duration": 4.0}
        ]
      }
    }
    
    Rules:
    - Notes format: "C#4", "Bb3", "F5". Use "REST" for silence.
    - Duration is in beats (0.25, 0.5, 1.0, 2.0, 4.0).
    - Ensure melody, bass, and chords have roughly the same total duration.
    - Be creative with the melody (don't just go up and down scales).
    """
    
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        content = [prompt, image]
        if audio_path:
            audio_file = genai.upload_file(path=audio_path)
            content.append(audio_file)
        
        # Add timeout to prevent hanging
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
                validate(instance=parsed_json, schema=MUSIC_JSON_SCHEMA)
                # Cache the successful composition
                composition_cache.set(image, parsed_json, audio_path)
                
                # Record metrics
                duration = time.time() - start_time
                metrics.record_api_call(duration, cached=False)
                log_user_action("composition_generated", {"tempo": parsed_json.get("tempo"), "mood": parsed_json.get("mood")})
                
                return parsed_json, "Composition IA générée avec succès."
            except ValidationError as ve:
                logger.error(f"JSON validation error: {ve}")
                metrics.record_error("validation", str(ve))
                return None, f"Erreur validation JSON: {ve.message}"
        
        return None, "Erreur format JSON Gemini"
    except Exception as e:
        logger.exception("API call failed")
        metrics.record_error("api", str(e))
        return None, f"Erreur API: {e}"

# --- GRADIO PROCESS ---

@track_time("process_image")
def process_image(image, audio, instrument_override, use_reverb, use_delay, use_compression):
    if not image: return None, None, None, None, None
    
    log_user_action("process_image", {"has_audio": audio is not None, "instrument": instrument_override})
    start_time = time.time()
    
    # Check import status
    if music_utils is None:
        return None, None, None, None, json.dumps({"error": "Server Error: music_utils failed to load", "details": music_utils_error}, indent=2)
    
    analysis, msg = analyze_with_gemini(image, audio)
    
    if not analysis:
        # Fallback
        logger.warning("Using fallback composition")
        analysis = {
            "mood": "Fallback Basic",
            "tempo": 120,
            "tracks": {
                "melody": [{"note": "C4", "duration": 1}, {"note": "E4", "duration": 1}, {"note": "G4", "duration": 2}],
                "bass": [{"note": "C2", "duration": 4}],
                "chords": [{"notes": ["C3", "E3", "G3"], "duration": 4}]
            }
        }
    
    inst = instrument_override if instrument_override != "Auto-Detect" else analysis.get('suggested_instrument', 'piano')
    
    # 1. Convert JSON -> Music21 Score
    score = music_utils.json_to_music21(analysis)
    
    # 2. Score -> ABC (pour édition/visu)
    abc_content = music_utils.music21_to_abc(score)
    
    # 3. Score -> Audio & MIDI
    audio_start = time.time()
    wav_data = music_utils.score_to_audio(score, inst)
    
    # 4. Apply audio effects
    sr, audio_array = wav_data
    audio_float = audio_array.astype(np.float32) / 32767.0
    
    processed_audio = audio_effects.apply_effects_chain(
        audio_float,
        use_reverb=use_reverb,
        use_delay=use_delay,
        use_compression=use_compression,
        room_size=0.6,
        delay_time=0.25,
        feedback=0.35,
        delay_mix=0.25
    )
    
    # Convert back to int16
    processed_audio_int16 = (processed_audio * 32767).astype(np.int16)
    wav_data = (sr, processed_audio_int16)
    
    metrics.record_audio_generation(time.time() - audio_start)
    
    midi_path = music_utils.score_to_midi(score)
    mp3_path = music_utils.save_audio_to_mp3(wav_data[0], wav_data[1])
    
    # Record total composition time
    metrics.record_composition(time.time() - start_time)
    
    return wav_data, abc_content, midi_path, mp3_path, json.dumps(analysis, indent=2)

@track_time("update_from_abc")
def update_from_abc(abc_content, instrument_override, use_reverb, use_delay, use_compression):
    """Callback quand l'utilisateur modifie le code ABC"""
    if not abc_content: return None, None, None
    
    log_user_action("update_from_abc", {"instrument": instrument_override})
    
    if music_utils is None:
        return None, None, None
    
    # 1. ABC -> Score
    score = music_utils.abc_to_music21(abc_content)
    if not score:
        return None, None, None
    
    inst = instrument_override if instrument_override != "Auto-Detect" else 'piano'
    
    # 2. Score -> Audio & MIDI
    wav_data = music_utils.score_to_audio(score, inst)
    
    # 3. Apply effects
    sr, audio_array = wav_data
    audio_float = audio_array.astype(np.float32) / 32767.0
    
    processed_audio = audio_effects.apply_effects_chain(
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
    
    return wav_data, midi_path, mp3_path

# --- UI SETUP ---

css = """
#paper {
    background: white;
    padding: 20px;
    border-radius: 8px;
    margin-top: 10px;
    min-height: 200px;
}
.gradio-container {
    font-family: 'Inter', sans-serif;
}
.metrics-box {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
}
"""

js_head = """
<script src="https://cdnjs.cloudflare.com/ajax/libs/abcjs/6.2.2/abcjs-basic-min.js"></script>
"""

def get_metrics_display():
    """Get formatted metrics for display."""
    stats = metrics.get_stats()
    return f"""
📊 **Statistiques de Performance**
- ⏱️ Uptime: {stats['uptime_formatted']}
- 🎵 Compositions: {stats['total_compositions']}
- 📞 Appels API: {stats['api_calls']}
- 💾 Taux de cache: {stats['cache_hit_rate']}
- ⚡ Temps API moyen: {stats['avg_api_response_time']}
- 🎼 Temps audio moyen: {stats['avg_audio_generation_time']}
- ❌ Erreurs: {stats['errors']}
"""

# Simplified setup to debug 500 error
# with gr.Blocks(title="Img2Music AI Composer", theme=gr.themes.Soft(), css=css, head=js_head) as demo:
with gr.Blocks(title="Img2Music AI Composer", css=css) as demo:
    # Inject JS manually via HTML component since 'head' might be causing issues
    gr.HTML(js_head)
    gr.Markdown("# 🎼 Img2Music: True AI Composer Pro")
    gr.Markdown("L'IA analyse l'image et écrit la partition. Vous pouvez ensuite **éditer la partition** et appliquer des **effets audio** professionnels !")
    
    with gr.Tabs():
        with gr.TabItem("🎨 Composer", id=0):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📥 Entrées")
                    input_img = gr.Image(type="pil", label="Image Inspiratrice", sources=["upload", "clipboard"])
                    input_audio = gr.Audio(type="filepath", label="Inspiration Audio (Optionnel)", sources=["upload", "microphone"])
                    
                    gr.Markdown("### 🎹 Configuration")
                    inst_drop = gr.Dropdown(
                        choices=["Auto-Detect", "piano", "synth_retro", "strings", "bass", "guitar", "brass", "drums"], 
                        value="Auto-Detect", 
                        label="Instrument Principal"
                    )
                    
                    gr.Markdown("### 🎚️ Effets Audio")
                    with gr.Row():
                        use_reverb = gr.Checkbox(label="🌊 Reverb", value=False)
                        use_delay = gr.Checkbox(label="🔁 Delay", value=False)
                        use_compression = gr.Checkbox(label="📊 Compression", value=True)
                    
                    btn_compose = gr.Button("✨ COMPOSER LA PARTITION IA", variant="primary", size="lg")
                    
                with gr.Column(scale=1):
                    gr.Markdown("### 🎵 Résultats")
                    # Sorties
                    out_audio = gr.Audio(label="Rendu Audio (Synth + Effets)")
                    with gr.Row():
                        out_midi = gr.File(label="📥 MIDI (.mid)")
                        out_mp3 = gr.File(label="📥 MP3 (.mp3)")
            
            gr.Markdown("### 📝 Éditeur de Partition (Format ABC)")
            abc_editor = gr.Code(language="markdown", label="Code ABC (Modifiable)", lines=10)
            btn_update = gr.Button("🔄 Mettre à jour Audio & Partition", variant="secondary")

            gr.Markdown("### 👁️ Partition Visuelle")
            html_score = gr.HTML('<div id="paper"></div>')
            
            # Debug JSON
            with gr.Accordion("🔍 Détails JSON (Debug)", open=False):
                out_json = gr.JSON()
        
        with gr.TabItem("📊 Métriques", id=1):
            gr.Markdown("## 📈 Tableau de Bord des Performances")
            metrics_display = gr.Markdown(get_metrics_display())
            btn_refresh_metrics = gr.Button("🔄 Actualiser les Métriques")
            
            gr.Markdown("### 📋 Statistiques Détaillées")
            metrics_json = gr.JSON(value=metrics.get_stats())
            
            def refresh_metrics():
                return get_metrics_display(), metrics.get_stats()
            
            btn_refresh_metrics.click(
                refresh_metrics,
                [],
                [metrics_display, metrics_json]
            )
        
        with gr.TabItem("ℹ️ Aide", id=2):
            gr.Markdown("""
            ## 🎼 Guide d'Utilisation
            
            ### 1. Composer une Musique
            1. **Uploadez une image** qui vous inspire
            2. (Optionnel) Ajoutez un **fichier audio** pour influencer le rythme
            3. Choisissez un **instrument** ou laissez l'IA décider
            4. Activez les **effets audio** souhaités
            5. Cliquez sur **COMPOSER LA PARTITION IA**
            
            ### 2. Éditer la Partition
            - Modifiez le code **ABC** dans l'éditeur
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
            - Consultez les **métriques** pour voir les performances
            - Les **logs** sont disponibles côté serveur
            """)

    # EVENTS
    
    # 1. Compose
    btn_compose.click(
        process_image, 
        [input_img, input_audio, inst_drop, use_reverb, use_delay, use_compression], 
        [out_audio, abc_editor, out_midi, out_mp3, out_json]
    )
    
    # 2. Update Audio/Midi from ABC
    btn_update.click(
        update_from_abc,
        [abc_editor, inst_drop, use_reverb, use_delay, use_compression],
        [out_audio, out_midi, out_mp3]
    )
    
    # 3. Update Visual Score (JS-only trigger on change or after generation)
    js_render_func = "(abc) => { if(abc) ABCJS.renderAbc('paper', abc, { responsive: 'resize' }); }"
    
    abc_editor.change(None, [abc_editor], None, js=js_render_func)

if __name__ == "__main__":
    try:
        logger.info("Starting Gradio server...")
        print("🚀 STARTING DEPLOYMENT V4.2 - SAFE MODE", flush=True)
        demo.launch(
            server_name="0.0.0.0", 
            server_port=7860
        )
        logger.info("Gradio server stopped.")
    except Exception as e:
        logger.critical(f"FAILED TO START GRADIO: {e}")
        print(f"❌ FATAL ERROR: {e}", flush=True)
        raise

