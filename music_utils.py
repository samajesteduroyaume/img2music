import os
import numpy as np
import tempfile

# --- PRE-CONFIG ENV ---
# Doit être fait avant d'importer d'autres modules music21 si possible, ou juste après
os.environ['MUSIC21_NO_PLAYBACK'] = '1'

import music21

# --- CONFIG MUSIC21 ---
try:
    # Force la config dans /tmp pour éviter les erreurs de permission
    music21.environment.set('directoryScratch', '/tmp')
    music21.environment.set('autoDownload', 'deny')
    music21.environment.set('writeFormat', 'musicxml') # Default safe
except Exception as e:
    print(f"Warning: Could not configure music21 environment: {e}")

# --- SYNTHÉTISEUR (Adapté de l'ancien code) ---

# --- SYNTHÉTISEUR (Amélioré pour meilleure qualité) ---
class SimpleSynthesizer:
    def __init__(self, sample_rate=44100):
        self.sr = sample_rate

    def get_wave(self, t, freq, instrument):
        if instrument == 'piano':
            # Piano amélioré avec plus d'harmoniques et enveloppe réaliste
            audio = 0.5 * np.sin(2 * np.pi * freq * t)
            audio += 0.3 * np.sin(2 * np.pi * freq * 2 * t) * np.exp(-t*3)
            audio += 0.2 * np.sin(2 * np.pi * freq * 3 * t) * np.exp(-t*5)
            audio += 0.1 * np.sin(2 * np.pi * freq * 4 * t) * np.exp(-t*7)
            audio += 0.05 * np.sin(2 * np.pi * freq * 5 * t) * np.exp(-t*9)
            # Ajout de bruit pour réalisme
            audio += 0.01 * np.random.randn(len(t)) * np.exp(-t*10)
            return audio * np.exp(-t*2)
        
        elif instrument == 'synth_retro':
            # Synthé rétro avec filtre passe-bas simulé
            phase = (freq * t) % 1.0
            square = 2.0 * (phase - 0.5)
            # Ajout d'une onde triangle pour adoucir
            triangle = 2.0 * np.abs(2.0 * (phase - 0.5)) - 1.0
            audio = 0.7 * square + 0.3 * triangle
            return audio * 0.5
        
        elif instrument == 'strings':
            # Cordes avec vibrato et plusieurs harmoniques
            vibrato = 1.0 + 0.02 * np.sin(2 * np.pi * 5 * t)  # 5Hz vibrato
            audio = 0.6 * np.sin(2 * np.pi * freq * vibrato * t)
            audio += 0.25 * np.sin(2 * np.pi * freq * 2 * vibrato * t)
            audio += 0.1 * np.sin(2 * np.pi * freq * 3 * vibrato * t)
            audio += 0.05 * np.sin(2 * np.pi * freq * 4 * vibrato * t)
            return audio * 0.8
        
        elif instrument == 'bass':
            # Basse avec sub-harmonique et saturation douce
            audio = 0.7 * np.sin(2 * np.pi * freq * t)
            audio += 0.3 * np.sin(2 * np.pi * freq * 0.5 * t)  # Sub octave
            # Saturation douce (tanh)
            audio = np.tanh(audio * 1.5)
            return audio * 0.6
        
        elif instrument == 'guitar':
            # Guitare acoustique avec harmoniques riches
            audio = 0.5 * np.sin(2 * np.pi * freq * t)
            audio += 0.3 * np.sin(2 * np.pi * freq * 2 * t)
            audio += 0.15 * np.sin(2 * np.pi * freq * 3 * t)
            audio += 0.1 * np.sin(2 * np.pi * freq * 4 * t)
            audio += 0.05 * np.sin(2 * np.pi * freq * 5 * t)
            # Ajout de bruit pour le picking
            audio += 0.02 * np.random.randn(len(t)) * np.exp(-t*15)
            return audio * 0.7
        
        elif instrument == 'brass':
            # Cuivres avec harmoniques impaires dominantes
            audio = 0.6 * np.sin(2 * np.pi * freq * t)
            audio += 0.4 * np.sin(2 * np.pi * freq * 3 * t)
            audio += 0.2 * np.sin(2 * np.pi * freq * 5 * t)
            audio += 0.1 * np.sin(2 * np.pi * freq * 7 * t)
            # Vibrato lent pour réalisme
            vibrato = 1.0 + 0.01 * np.sin(2 * np.pi * 4 * t)
            audio *= vibrato
            return audio * 0.75
        
        elif instrument == 'drums':
            # Percussion/kick drum (utilise freq comme pitch de base)
            # Kick drum avec sweep de fréquence
            freq_sweep = freq * (1 + 2 * np.exp(-t * 20))
            audio = np.sin(2 * np.pi * freq_sweep * t)
            # Ajout de bruit pour le snap
            audio += 0.3 * np.random.randn(len(t)) * np.exp(-t * 10)
            return audio * 0.8
        
        else:
            # Sinus pur par défaut
            return 0.5 * np.sin(2 * np.pi * freq * t)

    def generate_note(self, freq, duration, instrument='piano', velocity=1.0):
        t = np.linspace(0, duration, int(self.sr * duration), endpoint=False)
        raw_audio = self.get_wave(t, freq, instrument)
        
        # Enveloppes améliorées ADSR
        attack_time = min(0.01, duration * 0.1)  # 10ms ou 10% de la durée
        decay_time = min(0.05, duration * 0.15)
        release_time = min(0.1, duration * 0.2)
        
        attack_samples = int(attack_time * self.sr)
        decay_samples = int(decay_time * self.sr)
        release_samples = int(release_time * self.sr)
        
        env = np.ones_like(t)
        
        if instrument == 'strings':
            # Enveloppe ADSR pour cordes
            if len(env) > attack_samples:
                env[:attack_samples] = np.linspace(0, 1, attack_samples)
            if len(env) > attack_samples + decay_samples:
                env[attack_samples:attack_samples+decay_samples] = np.linspace(1, 0.8, decay_samples)
            if len(env) > release_samples:
                env[-release_samples:] *= np.linspace(1, 0, release_samples)
        
        elif instrument == 'piano':
            # Enveloppe exponentielle naturelle pour piano
            env = np.exp(-t * 2.5)
            # Attack rapide
            if len(env) > attack_samples:
                env[:attack_samples] *= np.linspace(0, 1, attack_samples)
        
        else:
            # Enveloppe générique avec fade in/out
            if len(env) > attack_samples:
                env[:attack_samples] *= np.linspace(0, 1, attack_samples)
            if len(env) > release_samples:
                env[-release_samples:] *= np.linspace(1, 0, release_samples)
        
        return raw_audio * env * velocity

# --- CONVERSION LOGIC ---

def json_to_music21(json_data):
    """Convertit le JSON généré par Gemini en un Score music21"""
    score = music21.stream.Score()
    
    # Metadata
    score.insert(0, music21.metadata.Metadata())
    score.metadata.title = f"AI Composition - {json_data.get('mood', 'Untitled')}"
    score.metadata.composer = "Img2Music AI"
    
    tempo_val = json_data.get('tempo', 120)
    score.insert(0, music21.tempo.MetronomeMark(number=tempo_val))
    
    tracks_data = json_data.get('tracks', {})
    
    # 1. Melody Part
    if 'melody' in tracks_data:
        p_melody = music21.stream.Part()
        p_melody.id = 'Melody'
        p_melody.insert(0, music21.instrument.Piano())
        
        for event in tracks_data['melody']:
            note_str = event.get('note')
            dur_val = float(event.get('duration', 1.0))
            
            if note_str == "REST":
                r = music21.note.Rest()
                r.quarterLength = dur_val
                p_melody.append(r)
            else:
                n = music21.note.Note(note_str)
                n.quarterLength = dur_val
                p_melody.append(n)
        score.insert(0, p_melody)

    # 2. Bass Part
    if 'bass' in tracks_data:
        p_bass = music21.stream.Part()
        p_bass.id = 'Bass'
        p_bass.insert(0, music21.instrument.ElectricBass())
        
        for event in tracks_data['bass']:
            note_str = event.get('note')
            dur_val = float(event.get('duration', 1.0))
            
            if note_str == "REST":
                r = music21.note.Rest()
                r.quarterLength = dur_val
                p_bass.append(r)
            else:
                n = music21.note.Note(note_str)
                n.quarterLength = dur_val
                p_bass.append(n)
        score.insert(0, p_bass)

    # 3. Chords Part
    if 'chords' in tracks_data:
        p_chords = music21.stream.Part()
        p_chords.id = 'Chords'
        p_chords.insert(0, music21.instrument.StringInstrument())
        
        for event in tracks_data['chords']:
            notes_list = event.get('notes', [])
            dur_val = float(event.get('duration', 2.0))
            
            if not notes_list or (len(notes_list) == 1 and notes_list[0] == "REST"):
                r = music21.note.Rest()
                r.quarterLength = dur_val
                p_chords.append(r)
            else:
                c = music21.chord.Chord(notes_list)
                c.quarterLength = dur_val
                p_chords.append(c)
        score.insert(0, p_chords)

    return score

def music21_to_abc(score):
    """Retourne la représentation ABC du score"""
    # Music21 a un exportateur ABC basic via write('abc') mais il écrit dans un fichier.
    # On va utiliser le converter
    
    # Alternative : utiliser une méthode native si disponible ou passer par un fichier temporaire
    # Le converter 'abc' de music21 n'est pas toujours parfait pour l'export string direct
    # On passe par un fichier tmp pour la fiabilité
    try:
        # Configuration minimale pour ABC
        abc_path = score.write('abc')
        with open(abc_path, 'r') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"Error converting to ABC: {e}")
        return "X:1\nT:Error\nK:C\nC"

def abc_to_music21(abc_content):
    """Parse le contenu ABC pour recréer un Score"""
    try:
        score = music21.converter.parse(abc_content, format='abc')
        return score
    except Exception as e:
        print(f"Error parsing ABC: {e}")
        return None

def score_to_midi(score):
    """Renvoie le chemin vers un fichier MIDI temporaire"""
    fp = score.write('midi')
    return fp

def score_to_audio(score, instrument_name='piano'):
    """Génère l'audio (numpy array) à partir du score"""
    # On doit "aplatir" le score pour le jouer linéairement ou mixer les parts
    # Music21 -> MIDI-like events -> Synth
    
    sr = 44100
    synth = SimpleSynthesizer(sr)
    
    # On va mixer les données audio
    # Pour simplifier, on crée un buffer assez large et on retaille à la fin
    # On estime la durée : score.duration.quarterLength (en noir) -> secondes
    
    mm = score.metronomeMarkBoundaries()[0][2] if score.metronomeMarkBoundaries() else music21.tempo.MetronomeMark(number=120)
    bpm = mm.number
    total_beats = score.duration.quarterLength
    total_seconds = (total_beats * 60) / bpm + 2 # +2s de marge
    
    buffer_len = int(total_seconds * sr)
    mix_buffer = np.zeros(buffer_len)
    
    parts = score.parts
    if not parts:
        parts = [score.flat] # Si pas de parts, on prend tout à plat

    for part in score.parts:
        # Determine instrument roughly based on part name or ID
        part_id = part.id.lower()
        inst = instrument_name # Par defaut utilisateur
        if 'bass' in part_id:
            inst = 'bass'
        elif 'chord' in part_id:
            inst = 'strings' if instrument_name == 'piano' else instrument_name
        elif 'melody' in part_id:
            inst = instrument_name
            
        # Flatten part to get offset/notes
        flat_part = part.flat
        
        for element in flat_part.notes:
            start_beat = element.offset
            duration_beat = element.quarterLength
            
            start_sec = (start_beat * 60) / bpm
            dur_sec = (duration_beat * 60) / bpm
            
            notes_to_play = []
            if element.isNote:
                notes_to_play.append(element)
            elif element.isChord:
                notes_to_play.extend(element.notes)
            
            for n in notes_to_play:
                freq = n.pitch.frequency
                audio = synth.generate_note(freq, dur_sec, inst)
                
                # Add to mix
                start_sample = int(start_sec * sr)
                end_sample = start_sample + len(audio)
                
                if end_sample > len(mix_buffer):
                     # Resize si trop court (ne devrait pas arriver souvent avec la marge)
                     new_mix = np.zeros(end_sample + sr)
                     new_mix[:len(mix_buffer)] = mix_buffer
                     mix_buffer = new_mix

                mix_buffer[start_sample:end_sample] += audio * 0.5 # Volume mix

    # Normalize
    max_val = np.max(np.abs(mix_buffer))
    if max_val > 0:
        mix_buffer = mix_buffer / max_val * 0.95
        
    audio_int16 = (mix_buffer * 32767).astype(np.int16)
    return sr, audio_int16

def save_audio_to_mp3(sr, audio_data):
    """Sauvegarde les données audio (numpy int16) en fichier MP3 temporaire"""
    try:
        from pydub import AudioSegment
        # Create AudioSegment from numpy array (requires explicit parameters)
        # int16 = 2 bytes per sample
        audio_segment = AudioSegment(
            data=audio_data.tobytes(), 
            sample_width=2, 
            frame_rate=sr, 
            channels=1
        )
        
        tmp_mp3 = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        # Close file to let pydub/ffmpeg write to it by path or file handle
        tmp_mp3.close()
        
        audio_segment.export(tmp_mp3.name, format="mp3")
        return tmp_mp3.name
    except Exception as e:
        print(f"Error saving MP3: {e}")
        return None
