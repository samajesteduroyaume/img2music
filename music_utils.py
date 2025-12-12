import os
import numpy as np
import tempfile
import subprocess
import wave

# --- PRE-CONFIG ENV ---
os.environ['MUSIC21_NO_PLAYBACK'] = '1'

import music21

# --- CONFIG MUSIC21 ---
try:
    music21.environment.set('directoryScratch', '/tmp')
    music21.environment.set('autoDownload', 'deny')
    music21.environment.set('writeFormat', 'musicxml')
except Exception as e:
    print(f"Warning: Could not configure music21 environment: {e}")

# --- HELPER: FIND SOUNDFONT ---
def get_soundfont_path():
    """Find the installed soundfont path."""
    # Common paths for fluid-soundfont-gm on Debian/Ubuntu/Streamlit Cloud
    paths = [
        "/usr/share/sounds/sf2/FluidR3_GM.sf2",
        "/usr/share/sounds/sf2/default.sf2",
        "/usr/share/sounds/sf2/TimGM6mb.sf2",  # Sometimes available
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

# --- CONVERSION LOGIC ---

def json_to_music21(json_data):
    """Convert Gemini JSON to Music21 Score."""
    score = music21.stream.Score()
    
    # Metadata
    score.insert(0, music21.metadata.Metadata())
    score.metadata.title = f"AI Composition - {json_data.get('mood', 'Untitled')}"
    score.metadata.composer = "Img2Music AI"
    
    tempo_val = json_data.get('tempo', 120)
    score.insert(0, music21.tempo.MetronomeMark(number=tempo_val))
    
    # Key Signature (if provided by AI)
    key_str = json_data.get('key')
    if key_str:
        try:
            score.insert(0, music21.key.Key(key_str))
        except:
            pass # Ignore invalid keys
            
    tracks_data = json_data.get('tracks', {})
    
    # Helper to create parts
    def create_part(part_name, instrument, notes_data, is_chord=False):
        p = music21.stream.Part()
        p.id = part_name
        p.insert(0, instrument)
        
        for event in notes_data:
            dur_val = float(event.get('duration', 1.0))
            
            if is_chord:
                notes_list = event.get('notes', [])
                if not notes_list or (len(notes_list) == 1 and notes_list[0] == "REST"):
                    elt = music21.note.Rest()
                else:
                    elt = music21.chord.Chord(notes_list)
            else:
                note_str = event.get('note')
                if note_str == "REST":
                    elt = music21.note.Rest()
                else:
                    elt = music21.note.Note(note_str)
            
            elt.quarterLength = dur_val
            p.append(elt)
            
        return p

    # 1. Melody
    if 'melody' in tracks_data:
        # Try to map suggested instrument to MIDI program
        # For now, default to Piano or user selection is handled at synthesis time
        # But for MIDI file quality, it's better to set it here if we knew it.
        # Since 'instrument' is passed to audio gen, we can perhaps set a default here.
        score.insert(0, create_part('Melody', music21.instrument.Piano(), tracks_data['melody']))

    # 2. Bass
    if 'bass' in tracks_data:
        score.insert(0, create_part('Bass', music21.instrument.ElectricBass(), tracks_data['bass']))

    # 3. Chords
    if 'chords' in tracks_data:
        # Strings for pads/chords often sounds good
        score.insert(0, create_part('Chords', music21.instrument.StringInstrument(), tracks_data['chords'], is_chord=True))

    return score

def music21_to_abc(score):
    """Convert Score to ABC format."""
    try:
        abc_path = score.write('abc')
        if abc_path and os.path.exists(abc_path):
            with open(abc_path, 'r') as f:
                content = f.read()
            return content
        else:
            raise Exception("ABC file not created")
    except Exception as e:
        print(f"Error converting to ABC: {e}")
        return "X:1\nT:Error\nK:C\nC"

def abc_to_music21(abc_content):
    """Parse ABC content to Score."""
    try:
        score = music21.converter.parse(abc_content, format='abc')
        return score
    except Exception as e:
        print(f"Error parsing ABC: {e}")
        return None

def score_to_midi(score):
    """Write Score to temporary MIDI file."""
    fp = score.write('midi')
    return fp

def score_to_audio(score, instrument_name='piano'):
    """
    Generate audio from score using FluidSynth.
    Returns: (sample_rate, numpy_int16_array)
    """
    sf2_path = get_soundfont_path()
    if not sf2_path:
        print("❌ Error: No SoundFont found. Install fluid-soundfont-gm.")
        # Fallback to silent/empty audio or raise error?
        # Let's return 1s of silence to avoid crash
        return 44100, np.zeros(44100, dtype=np.int16)

    # 1. Set instruments based on request
    # This is tricky because music21 parts already have instruments.
    # The 'instrument_name' arg usually overrides the melody instrument.
    
    # Map common suggestions to General MIDI program numbers
    midi_programs = {
        'piano': 0,          # Acoustic Grand Piano
        'synth_retro': 81,   # Lead 2 (sawtooth) - roughly retro
        'strings': 48,       # String Ensemble 1
        'bass': 33,          # Electric Bass (finger)
        'guitar': 25,        # Acoustic Guitar (nylon)
        'brass': 61,         # Brass Section
        'drums': 0,          # Drums are channel 10, program doesn't matter much usually
        'sax': 65,           # Alto Sax
        'flute': 73,         # Flute
    }
    
    prog = midi_programs.get(instrument_name, 0)
    
    # Update the first part (Melody) instrument
    if len(score.parts) > 0:
        p0 = score.parts[0]
        # Remove existing instrument objects at start
        p0.removeByClass('Instrument')
        
        new_inst = music21.instrument.instrumentFromMidiProgram(prog)
        p0.insert(0, new_inst)

    # 2. Export to MIDI
    midi_path = score.write('midi')
    
    # 3. Render with FluidSynth
    # fluidsynth -ni -g 1.0 /path/to/sf2 midifile -F output.wav -r 44100
    tmp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
    
    cmd = [
        'fluidsynth',
        '-ni',              # No interactive shell
        '-g', '1.0',       # Gain
        sf2_path,
        midi_path,
        '-F', tmp_wav,      # Fast render to file
        '-r', '44100'       # Sample rate
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        
        # 4. Read WAV back to numpy
        if os.path.exists(tmp_wav):
            with wave.open(tmp_wav, 'rb') as wf:
                sr = wf.getframerate()
                # Read all frames
                n_frames = wf.getnframes()
                audio_bytes = wf.readframes(n_frames)
                
                # Convert to numpy
                audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
                
                # If stereo, mix to mono or keep stereo?
                # App expects (sr, data). Data can be 1D or 2D. 
                # Wav file from fluidsynth is likely stereo.
                channels = wf.getnchannels()
                if channels == 2:
                    audio_data = audio_data.reshape(-1, 2)
                    # Mix to mono for simple visualization/effects later?
                    # Or keep stereo. Let's keep stereo if possible, but audio_effects Might expect mono.
                    # Looking at audio_effects.py: it does simple math. If input is (N, 2), it works?
                    # "if delay < len(audio)" -> len matches samples (N).
                    # "audio[:-delay]" -> works for (N, 2).
                    # So stereo should be fine!
                
            os.remove(tmp_wav)
            return sr, audio_data
        else:
            print("FluidSynth did not create output file.")
            return 44100, np.zeros(44100, dtype=np.int16)
            
    except subprocess.CalledProcessError as e:
        print(f"FluidSynth error: {e.stderr.decode()}")
        return 44100, np.zeros(44100, dtype=np.int16)
    except Exception as e:
        print(f"Error processing audio: {e}")
        return 44100, np.zeros(44100, dtype=np.int16)

def save_audio_to_mp3(sr, audio_data):
    """Save audio data to MP3 using ffmpeg."""
    try:
        # Handle Stereo/Mono for saving
        channels = 1
        if len(audio_data.shape) > 1 and audio_data.shape[1] == 2:
            channels = 2
            
        tmp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        tmp_wav.close()

        with wave.open(tmp_wav.name, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sr)
            wav_file.writeframes(audio_data.tobytes())

        tmp_mp3 = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        tmp_mp3.close()

        cmd = [
            'ffmpeg', '-y', '-i', tmp_wav.name,
            '-acodec', 'libmp3lame', '-q:a', '2', tmp_mp3.name
        ]

        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        os.unlink(tmp_wav.name)

        return tmp_mp3.name
    except Exception as e:
        print(f"Error saving MP3: {e}")
        return None
