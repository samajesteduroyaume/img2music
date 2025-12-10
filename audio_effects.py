"""
Audio effects processing for img2music.
Provides reverb, delay, EQ, and compression effects.
"""
import numpy as np
from typing import Tuple


class AudioEffects:
    """Audio effects processor."""
    
    def __init__(self, sample_rate: int = 44100):
        self.sr = sample_rate
    
    def apply_reverb(self, audio: np.ndarray, room_size: float = 0.5, damping: float = 0.5) -> np.ndarray:
        """
        Apply simple reverb effect using comb filters.
        
        Args:
            audio: Input audio array
            room_size: Room size (0.0 to 1.0)
            damping: High frequency damping (0.0 to 1.0)
        
        Returns:
            Audio with reverb applied
        """
        # Simple Schroeder reverb with comb filters
        delays = [int(self.sr * d) for d in [0.0297, 0.0371, 0.0411, 0.0437]]
        gains = [0.7, 0.7, 0.7, 0.7]
        
        output = audio.copy()
        
        for delay, gain in zip(delays, gains):
            delay = int(delay * (0.5 + room_size * 0.5))
            if delay < len(audio):
                delayed = np.zeros_like(audio)
                delayed[delay:] = audio[:-delay] * gain * (1 - damping)
                output += delayed
        
        # Normalize
        max_val = np.max(np.abs(output))
        if max_val > 0:
            output = output / max_val * 0.95
        
        return output
    
    def apply_delay(self, audio: np.ndarray, delay_time: float = 0.3, feedback: float = 0.4, mix: float = 0.3) -> np.ndarray:
        """
        Apply delay effect.
        
        Args:
            audio: Input audio array
            delay_time: Delay time in seconds
            feedback: Feedback amount (0.0 to 0.9)
            mix: Dry/wet mix (0.0 to 1.0)
        
        Returns:
            Audio with delay applied
        """
        delay_samples = int(delay_time * self.sr)
        
        if delay_samples >= len(audio):
            return audio
        
        output = audio.copy()
        delayed = np.zeros_like(audio)
        
        # Create delay line with feedback
        for i in range(delay_samples, len(audio)):
            delayed[i] = audio[i - delay_samples] + delayed[i - delay_samples] * feedback
        
        # Mix dry and wet signals
        output = audio * (1 - mix) + delayed * mix
        
        # Normalize
        max_val = np.max(np.abs(output))
        if max_val > 0:
            output = output / max_val * 0.95
        
        return output
    
    def apply_eq(self, audio: np.ndarray, low_gain: float = 1.0, mid_gain: float = 1.0, high_gain: float = 1.0) -> np.ndarray:
        """
        Apply simple 3-band EQ.
        
        Args:
            audio: Input audio array
            low_gain: Low frequency gain (0.0 to 2.0)
            mid_gain: Mid frequency gain (0.0 to 2.0)
            high_gain: High frequency gain (0.0 to 2.0)
        
        Returns:
            Audio with EQ applied
        """
        # Simple frequency-based EQ using FFT
        fft = np.fft.rfft(audio)
        freqs = np.fft.rfftfreq(len(audio), 1/self.sr)
        
        # Define frequency bands
        low_cutoff = 250
        high_cutoff = 4000
        
        # Apply gains
        for i, freq in enumerate(freqs):
            if freq < low_cutoff:
                fft[i] *= low_gain
            elif freq < high_cutoff:
                fft[i] *= mid_gain
            else:
                fft[i] *= high_gain
        
        # Convert back to time domain
        output = np.fft.irfft(fft, len(audio))
        
        # Normalize
        max_val = np.max(np.abs(output))
        if max_val > 0:
            output = output / max_val * 0.95
        
        return output
    
    def apply_compression(self, audio: np.ndarray, threshold: float = 0.5, ratio: float = 4.0) -> np.ndarray:
        """
        Apply dynamic range compression.
        
        Args:
            audio: Input audio array
            threshold: Compression threshold (0.0 to 1.0)
            ratio: Compression ratio (1.0 to 20.0)
        
        Returns:
            Compressed audio
        """
        output = audio.copy()
        
        # Simple compression
        mask = np.abs(output) > threshold
        excess = np.abs(output[mask]) - threshold
        output[mask] = np.sign(output[mask]) * (threshold + excess / ratio)
        
        # Make-up gain
        makeup_gain = 1.0 / (1.0 - (1.0 - 1.0/ratio) * 0.5)
        output *= makeup_gain
        
        # Normalize
        max_val = np.max(np.abs(output))
        if max_val > 0:
            output = output / max_val * 0.95
        
        return output
    
    def apply_effects_chain(
        self, 
        audio: np.ndarray,
        use_reverb: bool = False,
        use_delay: bool = False,
        use_eq: bool = False,
        use_compression: bool = True,
        **effect_params
    ) -> np.ndarray:
        """
        Apply a chain of effects to audio.
        
        Args:
            audio: Input audio
            use_reverb: Enable reverb
            use_delay: Enable delay
            use_eq: Enable EQ
            use_compression: Enable compression
            **effect_params: Parameters for each effect
        
        Returns:
            Processed audio
        """
        output = audio.copy()
        
        # Apply effects in order
        if use_eq:
            output = self.apply_eq(
                output,
                low_gain=effect_params.get('low_gain', 1.0),
                mid_gain=effect_params.get('mid_gain', 1.0),
                high_gain=effect_params.get('high_gain', 1.0)
            )
        
        if use_compression:
            output = self.apply_compression(
                output,
                threshold=effect_params.get('threshold', 0.5),
                ratio=effect_params.get('ratio', 4.0)
            )
        
        if use_delay:
            output = self.apply_delay(
                output,
                delay_time=effect_params.get('delay_time', 0.3),
                feedback=effect_params.get('feedback', 0.4),
                mix=effect_params.get('delay_mix', 0.3)
            )
        
        if use_reverb:
            output = self.apply_reverb(
                output,
                room_size=effect_params.get('room_size', 0.5),
                damping=effect_params.get('damping', 0.5)
            )
        
        return output
