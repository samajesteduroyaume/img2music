"""
Simple in-memory cache for Gemini API responses.
Reduces API calls and costs by caching compositions based on image hash.
"""
import hashlib
import time
from typing import Optional, Dict, Any
from PIL import Image
import io


class CompositionCache:
    """In-memory cache for AI-generated compositions."""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Initialize the cache.
        
        Args:
            max_size: Maximum number of cached items
            ttl_seconds: Time-to-live for cache entries (default: 1 hour)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
    
    def _get_image_hash(self, image: Image.Image) -> str:
        """Generate a hash from an image for cache key."""
        # Convert image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
        
        # Generate SHA256 hash
        return hashlib.sha256(img_bytes).hexdigest()
    
    def get(self, image: Image.Image, audio_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached composition.
        
        Args:
            image: PIL Image object
            audio_path: Optional path to audio file
            
        Returns:
            Cached composition data or None if not found/expired
        """
        cache_key = self._get_image_hash(image)
        if audio_path:
            cache_key += f"_audio_{hashlib.md5(audio_path.encode()).hexdigest()}"
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            
            # Check if expired
            if time.time() - entry['timestamp'] > self.ttl_seconds:
                del self.cache[cache_key]
                return None
            
            return entry['data']
        
        return None
    
    def set(self, image: Image.Image, composition: Dict[str, Any], audio_path: Optional[str] = None):
        """
        Store a composition in the cache.
        
        Args:
            image: PIL Image object
            composition: Composition data to cache
            audio_path: Optional path to audio file
        """
        cache_key = self._get_image_hash(image)
        if audio_path:
            cache_key += f"_audio_{hashlib.md5(audio_path.encode()).hexdigest()}"
        
        # Implement LRU eviction if cache is full
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]
        
        self.cache[cache_key] = {
            'data': composition,
            'timestamp': time.time()
        }
    
    def clear(self):
        """Clear all cached entries."""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'ttl_seconds': self.ttl_seconds,
            'oldest_entry_age': min(
                [time.time() - entry['timestamp'] for entry in self.cache.values()],
                default=0
            )
        }
