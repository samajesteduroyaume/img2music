import gradio as gr
import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv
import pillow_heif

# Safe import for music_utils (to prevent 500 Global Error if music21 fails)
music_utils = None
music_utils_error = None
try:
    import music_utils
except Exception as e:
    music_utils_error = str(e)
    print(f"CRITICAL ERROR IMPORTING MUSIC_UTILS: {e}")

# Register HEIF opener
pillow_heif.register_heif_opener()

# Charger les variables d'environnement
load_dotenv()

# Configuration Gemini
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# --- LOGIQUE IA ---
def analyze_with_gemini(image, audio_path=None):
    if not API_KEY:
        return None, "⚠️ Configurez GEMINI_API_KEY."
    
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
            
        response = model.generate_content(content)
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            return json.loads(match.group(0)), "Composition IA générée avec succès."
        return None, "Erreur format JSON Gemini"
    except Exception as e:
        return None, f"Erreur API: {e}"

# --- GRADIO PROCESS ---

def process_image(image, audio, instrument_override):
    if not image: return None, None, None, None
    
    # Check import status
    if music_utils is None:
        return None, None, None, json.dumps({"error": "Server Error: music_utils failed to load", "details": music_utils_error}, indent=2)
    
    analysis, msg = analyze_with_gemini(image, audio)
    
    if not analysis:
        # Fallback
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
    wav_data = music_utils.score_to_audio(score, inst)
    midi_path = music_utils.score_to_midi(score)
    
    return wav_data, abc_content, midi_path, json.dumps(analysis, indent=2)

def update_from_abc(abc_content, instrument_override):
    """Callback quand l'utilisateur modifie le code ABC"""
    if not abc_content: return None, None
    
    if music_utils is None:
        return None, None # Could return error but Gradio blocks expect specific types
    
    # 1. ABC -> Score
    score = music_utils.abc_to_music21(abc_content)
    if not score:
        return None, None # Error handling ? behavior
    
    inst = instrument_override if instrument_override != "Auto-Detect" else 'piano'
    
    # 2. Score -> Audio & MIDI
    wav_data = music_utils.score_to_audio(score, inst)
    midi_path = music_utils.score_to_midi(score)
    
    return wav_data, midi_path

# --- UI SETUP ---

css = """
#paper {
    background: white;
    padding: 20px;
    border-radius: 8px;
    margin-top: 10px;
    min-height: 200px;
}
"""

js_head = """
<script src="https://cdnjs.cloudflare.com/ajax/libs/abcjs/6.2.2/abcjs-basic-min.js"></script>
"""

with gr.Blocks(title="Img2Music AI Composer", css=css, head=js_head) as demo:
    gr.Markdown("# 🎼 Img2Music: True AI Composer")
    gr.Markdown("L'IA analyse l'image et écrit la partition. Vous pouvez ensuite **éditer la partition** ci-dessous pour modifier la musique !")
    
    with gr.Row():
        with gr.Column(scale=1):
            input_img = gr.Image(type="pil", label="Image Inspiratrice", sources=["upload", "clipboard"])
            input_audio = gr.Audio(type="filepath", label="Inspiration Audio (Optionnel)", sources=["upload", "microphone"])
            inst_drop = gr.Dropdown(
                choices=["Auto-Detect", "piano", "synth_retro", "strings", "bass"], 
                value="Auto-Detect", label="Instrument"
            )
            btn_compose = gr.Button("✨ COMPOSER LA PARTITION IA", variant="primary")
            
        with gr.Column(scale=1):
            # Sorties
            out_audio = gr.Audio(label="Rendu Audio (Synth)")
            out_midi = gr.File(label="Télécharger MIDI")
            
            # Editeur ABC
            gr.Markdown("### 📝 Éditeur de Partition (Format ABC)")
            abc_editor = gr.Code(language="markdown", label="Code ABC (Modifiable)", lines=10)
            btn_update = gr.Button("🔄 Mettre à jour Audio & Partition", variant="secondary")

    gr.Markdown("### 👁️ Partition Visuelle")
    html_score = gr.HTML('<div id="paper"></div>')
    
    # Debug JSON
    with gr.Accordion("Détails JSON (Debug)", open=False):
        out_json = gr.JSON()

    # EVENTS
    
    # 1. Compose
    btn_compose.click(
        process_image, 
        [input_img, input_audio, inst_drop], 
        [out_audio, abc_editor, out_midi, out_json]
    )
    
    # 2. Update Audio/Midi from ABC
    btn_update.click(
        update_from_abc,
        [abc_editor, inst_drop],
        [out_audio, out_midi]
    )
    
    # 3. Update Visual Score (JS-only trigger on change or after generation)
    # On utilise un event JS pour le rendu ABCJS
    # Quand 'abc_editor' change, on met à jour le div paper
    
    js_render_func = "(abc) => { if(abc) ABCJS.renderAbc('paper', abc, { responsive: 'resize' }); }"
    
    abc_editor.change(None, [abc_editor], None, js=js_render_func)
    
    # Aussi déclencher le rendu après le click 'compose' (quand abc_editor reçoit la valeur)
    # Note: .success ou en chainant ne marche pas tjs pour le JS direct sur output, 
    # mais le change listener devrait l'attraper.

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
