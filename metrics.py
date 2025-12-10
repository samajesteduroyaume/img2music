"""
Logging and metrics system for img2music.
Provides structured logging and performance monitoring.
"""
import logging
import time
import json
from functools import wraps
from typing import Dict, Any, Optional
from datetime import datetime
import os


# Configure logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)

logger = logging.getLogger('img2music')


class MetricsCollector:
    """Collect and track application metrics."""
    
    def __init__(self):
        self.metrics = {
            'api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'compositions_generated': 0,
            'errors': 0,
            'total_processing_time': 0.0,
            'api_response_times': [],
            'audio_generation_times': [],
        }
        self.start_time = time.time()
    
    def record_api_call(self, duration: float, cached: bool = False):
        """Record an API call."""
        if cached:
            self.metrics['cache_hits'] += 1
            logger.info(f"Cache hit - instant response")
        else:
            self.metrics['cache_misses'] += 1
            self.metrics['api_calls'] += 1
            self.metrics['api_response_times'].append(duration)
            logger.info(f"API call completed in {duration:.2f}s")
    
    def record_composition(self, duration: float):
        """Record a composition generation."""
        self.metrics['compositions_generated'] += 1
        self.metrics['total_processing_time'] += duration
        logger.info(f"Composition generated in {duration:.2f}s")
    
    def record_audio_generation(self, duration: float):
        """Record audio generation time."""
        self.metrics['audio_generation_times'].append(duration)
        logger.debug(f"Audio generated in {duration:.2f}s")
    
    def record_error(self, error_type: str, error_msg: str):
        """Record an error."""
        self.metrics['errors'] += 1
        logger.error(f"{error_type}: {error_msg}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        uptime = time.time() - self.start_time
        
        avg_api_time = (
            sum(self.metrics['api_response_times']) / len(self.metrics['api_response_times'])
            if self.metrics['api_response_times'] else 0
        )
        
        avg_audio_time = (
            sum(self.metrics['audio_generation_times']) / len(self.metrics['audio_generation_times'])
            if self.metrics['audio_generation_times'] else 0
        )
        
        cache_hit_rate = (
            self.metrics['cache_hits'] / (self.metrics['cache_hits'] + self.metrics['cache_misses'])
            if (self.metrics['cache_hits'] + self.metrics['cache_misses']) > 0 else 0
        )
        
        return {
            'uptime_seconds': uptime,
            'uptime_formatted': f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m",
            'total_compositions': self.metrics['compositions_generated'],
            'api_calls': self.metrics['api_calls'],
            'cache_hit_rate': f"{cache_hit_rate * 100:.1f}%",
            'cache_hits': self.metrics['cache_hits'],
            'cache_misses': self.metrics['cache_misses'],
            'errors': self.metrics['errors'],
            'avg_api_response_time': f"{avg_api_time:.2f}s",
            'avg_audio_generation_time': f"{avg_audio_time:.2f}s",
            'total_processing_time': f"{self.metrics['total_processing_time']:.2f}s"
        }
    
    def get_stats_json(self) -> str:
        """Get statistics as JSON string."""
        return json.dumps(self.get_stats(), indent=2)


# Global metrics collector
metrics = MetricsCollector()


def track_time(metric_name: str):
    """Decorator to track execution time of functions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                logger.debug(f"{func.__name__} completed in {duration:.2f}s")
                return result
            except Exception as e:
                duration = time.time() - start
                metrics.record_error(func.__name__, str(e))
                logger.exception(f"{func.__name__} failed after {duration:.2f}s")
                raise
        return wrapper
    return decorator


def log_user_action(action: str, details: Optional[Dict] = None):
    """Log a user action."""
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'details': details or {}
    }
    logger.info(f"User action: {json.dumps(log_data)}")
