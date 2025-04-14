import uuid
import time
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import hashlib
import redis
from fastapi import Request
from ..config import settings
from .constants import CACHE_KEY_PREFIX

# Setup logging
logger = logging.getLogger("llm_gateway")

def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())

def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat() + "Z"

def calculate_hash(data: Any) -> str:
    """Calculate a hash of the input data for caching."""
    if isinstance(data, dict):
        # Sort the dict to ensure consistent hashing
        data = json.dumps(data, sort_keys=True)
    return hashlib.sha256(str(data).encode()).hexdigest()

def create_cache_key(prefix: str, data: Any) -> str:
    """Create a cache key from a prefix and data."""
    return f"{CACHE_KEY_PREFIX}{prefix}:{calculate_hash(data)}"

# Redis connection (lazy loaded)
_redis_client = None

def get_redis_client() -> Optional[redis.Redis]:
    """Get a Redis client if Redis is configured."""
    global _redis_client
    if not settings.REDIS_URL:
        return None
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.REDIS_URL)
            # Test connection
            _redis_client.ping()
        except redis.RedisError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            _redis_client = None
    return _redis_client

async def cache_get(key: str) -> Optional[Any]:
    """Get a value from the cache."""
    if not settings.CACHE_ENABLED:
        return None
    
    redis_client = get_redis_client()
    if redis_client:
        try:
            value = redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
    return None

async def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set a value in the cache."""
    if not settings.CACHE_ENABLED:
        return False
    
    ttl = ttl or settings.CACHE_TTL_SECONDS
    redis_client = get_redis_client()
    if redis_client:
        try:
            redis_client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
    return False

def is_rate_limited(key: str, max_requests: int, window_seconds: int) -> bool:
    """Check if a key is rate limited."""
    if not settings.RATE_LIMIT_ENABLED:
        return False
    
    redis_client = get_redis_client()
    if not redis_client:
        return False
    
    try:
        current = redis_client.get(f"rate:{key}")
        if current and int(current) >= max_requests:
            return True
        
        pipeline = redis_client.pipeline()
        pipeline.incr(f"rate:{key}")
        pipeline.expire(f"rate:{key}", window_seconds)
        pipeline.execute()
        return False
    except Exception as e:
        logger.error(f"Error checking rate limit: {str(e)}")
        return False

def get_client_ip(request: Request) -> str:
    """Get the client IP address from a request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def truncate_string(text: str, max_length: int = 100) -> str:
    """Truncate a string to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def log_request(request_id: str, endpoint: str, client_ip: str, params: Dict[str, Any]) -> None:
    """Log information about an incoming request."""
    logger.info(
        f"Request {request_id} | Endpoint: {endpoint} | Client: {client_ip} | "
        f"Params: {truncate_string(str(params))}"
    )

def log_response(request_id: str, status_code: int, duration_ms: float) -> None:
    """Log information about an outgoing response."""
    logger.info(
        f"Response {request_id} | Status: {status_code} | Duration: {duration_ms:.2f}ms"
    )

def log_error(request_id: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """Log detailed information about an error."""
    logger.error(
        f"Error {request_id} | Type: {type(error).__name__} | Message: {str(error)} | "
        f"Context: {context or {}}"
    )

def get_provider_mapping() -> Dict[str, List[str]]:
    """
    Get a mapping of model names to their compatible providers.
    This mapping helps the service factory determine which provider 
    should be used for a specific model.
    
    Returns:
        A dictionary mapping provider names to lists of compatible model IDs.
    """
    # This would ideally be loaded from a database or configuration file
    # For now, we hardcode the mapping for demonstration purposes
    mapping = {
        "ollama": [
            "llama3.2:1b",
            "llama2",
            "mistral",
            "codellama",
            "phi",
            "gemma"
        ]
    }
    
    # Try to load additional mappings from settings if available
    try:
        if hasattr(settings, "PROVIDER_MODEL_MAPPING") and settings.PROVIDER_MODEL_MAPPING:
            # Merge with the hardcoded mapping
            for provider, models in settings.PROVIDER_MODEL_MAPPING.items():
                if provider not in mapping:
                    mapping[provider] = []
                if isinstance(models, list):
                    mapping[provider].extend(models)
                elif isinstance(models, str):
                    mapping[provider].append(models)
    except ImportError:
        pass
    
    return mapping

def get_compatible_providers(model_id: str) -> List[str]:
    """
    Get a list of providers that are compatible with the specified model.
    
    Args:
        model_id: The ID of the model.
    
    Returns:
        A list of provider names that can handle the model.
    """
    mapping = get_provider_mapping()
    providers = []
    
    for provider, models in mapping.items():
        if model_id in models:
            providers.append(provider)
    
    return providers 