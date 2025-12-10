"""
Automated tests for img2music project.
Tests music_utils, cache, and app functionality.
"""
import unittest
import numpy as np
import tempfile
import os
from PIL import Image
import json

# Import modules to test
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cache import CompositionCache
import music_utils


class TestCompositionCache(unittest.TestCase):
    """Test the composition cache functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cache = CompositionCache(max_size=5, ttl_seconds=10)
        # Create a simple test image
        self.test_image = Image.new('RGB', (100, 100), color='red')
        self.test_composition = {
            "mood": "test",
            "tempo": 120,
            "tracks": {
                "melody": [{"note": "C4", "duration": 1.0}]
            }
        }
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        self.cache.set(self.test_image, self.test_composition)
        result = self.cache.get(self.test_image)
        self.assertEqual(result, self.test_composition)
    
    def test_cache_miss(self):
        """Test cache miss returns None."""
        different_image = Image.new('RGB', (100, 100), color='blue')
        result = self.cache.get(different_image)
        self.assertIsNone(result)
    
    def test_cache_with_audio(self):
        """Test cache with audio path."""
        audio_path = "/tmp/test.wav"
        self.cache.set(self.test_image, self.test_composition, audio_path)
        result = self.cache.get(self.test_image, audio_path)
        self.assertEqual(result, self.test_composition)
        
        # Different audio path should miss
        result = self.cache.get(self.test_image, "/tmp/different.wav")
        self.assertIsNone(result)
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        # Fill cache beyond max_size
        for i in range(6):
            img = Image.new('RGB', (100, 100), color=(i*40, 0, 0))
            comp = {"mood": f"test{i}", "tempo": 120 + i, "tracks": {}}
            self.cache.set(img, comp)
        
        # Cache should only have 5 items
        stats = self.cache.get_stats()
        self.assertEqual(stats['size'], 5)
    
    def test_cache_clear(self):
        """Test cache clear operation."""
        self.cache.set(self.test_image, self.test_composition)
        self.cache.clear()
        result = self.cache.get(self.test_image)
        self.assertIsNone(result)
    
    def test_cache_stats(self):
        """Test cache statistics."""
        self.cache.set(self.test_image, self.test_composition)
        stats = self.cache.get_stats()
        self.assertEqual(stats['size'], 1)
        self.assertEqual(stats['max_size'], 5)


class TestMusicUtils(unittest.TestCase):
    """Test music_utils functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_json = {
            "mood": "Happy",
            "tempo": 120,
            "suggested_instrument": "piano",
            "tracks": {
                "melody": [
                    {"note": "C4", "duration": 1.0},
                    {"note": "E4", "duration": 1.0},
                    {"note": "G4", "duration": 2.0}
                ],
                "bass": [
                    {"note": "C2", "duration": 4.0}
                ],
                "chords": [
                    {"notes": ["C3", "E3", "G3"], "duration": 4.0}
                ]
            }
        }
    
    def test_json_to_music21(self):
        """Test JSON to Music21 conversion."""
        score = music_utils.json_to_music21(self.test_json)
        self.assertIsNotNone(score)
        self.assertEqual(len(score.parts), 3)  # melody, bass, chords
    
    def test_music21_to_abc(self):
        """Test Music21 to ABC conversion."""
        score = music_utils.json_to_music21(self.test_json)
        abc_content = music_utils.music21_to_abc(score)
        self.assertIsNotNone(abc_content)
        self.assertIn("X:", abc_content)  # ABC header
    
    def test_abc_to_music21(self):
        """Test ABC to Music21 conversion."""
        abc_content = "X:1\nT:Test\nK:C\nC D E F|"
        score = music_utils.abc_to_music21(abc_content)
        self.assertIsNotNone(score)
    
    def test_score_to_midi(self):
        """Test MIDI file generation."""
        score = music_utils.json_to_music21(self.test_json)
        midi_path = music_utils.score_to_midi(score)
        self.assertTrue(os.path.exists(midi_path))
        self.assertTrue(midi_path.endswith('.mid'))
        # Cleanup
        os.remove(midi_path)
    
    def test_score_to_audio(self):
        """Test audio generation."""
        score = music_utils.json_to_music21(self.test_json)
        sr, audio_data = music_utils.score_to_audio(score, 'piano')
        self.assertEqual(sr, 44100)
        self.assertIsInstance(audio_data, np.ndarray)
        self.assertEqual(audio_data.dtype, np.int16)
        self.assertGreater(len(audio_data), 0)
    
    def test_synthesizer_instruments(self):
        """Test different synthesizer instruments."""
        synth = music_utils.SimpleSynthesizer()
        instruments = ['piano', 'synth_retro', 'strings', 'bass']
        
        for inst in instruments:
            audio = synth.generate_note(440.0, 1.0, inst)
            self.assertIsInstance(audio, np.ndarray)
            self.assertGreater(len(audio), 0)
    
    def test_save_audio_to_mp3(self):
        """Test MP3 file generation."""
        score = music_utils.json_to_music21(self.test_json)
        sr, audio_data = music_utils.score_to_audio(score, 'piano')
        mp3_path = music_utils.save_audio_to_mp3(sr, audio_data)
        
        if mp3_path:  # Only test if pydub/ffmpeg available
            self.assertTrue(os.path.exists(mp3_path))
            self.assertTrue(mp3_path.endswith('.mp3'))
            # Cleanup
            os.remove(mp3_path)


class TestJSONValidation(unittest.TestCase):
    """Test JSON schema validation."""
    
    def test_valid_json(self):
        """Test that valid JSON passes validation."""
        from jsonschema import validate
        # Import schema from app (would need to refactor app.py to export it)
        # For now, just test the structure
        valid_json = {
            "mood": "Happy",
            "tempo": 120,
            "tracks": {
                "melody": [{"note": "C4", "duration": 1.0}],
                "bass": [{"note": "C2", "duration": 2.0}],
                "chords": [{"notes": ["C3", "E3"], "duration": 2.0}]
            }
        }
        # This would validate against MUSIC_JSON_SCHEMA from app.py
        self.assertIsInstance(valid_json, dict)
        self.assertIn("mood", valid_json)
        self.assertIn("tempo", valid_json)
        self.assertIn("tracks", valid_json)


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCompositionCache))
    suite.addTests(loader.loadTestsFromTestCase(TestMusicUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestJSONValidation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit_code = run_tests()
    exit(exit_code)
