from enum import Enum, auto

class ProviderType(str, Enum):
    """Enum for supported LLM providers."""
    OLLAMA = "ollama"
    # Add more providers as needed

class ModelCapability(str, Enum):
    """Enum for model capabilities."""
    CHAT = "chat"
    EMBEDDING = "embedding"
    COMPLETION = "completion"

class ErrorCode(str, Enum):
    """Error codes for the API responses."""
    INVALID_REQUEST = "invalid_request"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    PROVIDER_ERROR = "provider_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    MODEL_NOT_FOUND = "model_not_found"
    INTERNAL_SERVER_ERROR = "internal_server_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    TIMEOUT_ERROR = "timeout_error"

# Default token limits for different model types
DEFAULT_TOKEN_LIMITS = {
    "chat": 4096,
    "embedding": 8192,
    "completion": 4096,
}

# Retry configuration for provider requests
RETRY_ATTEMPTS = 3
RETRY_MIN_SECONDS = 1
RETRY_MAX_SECONDS = 10

# Cache constants
CACHE_KEY_PREFIX = "llm_gateway:"
CACHE_MODEL_INFO_TTL = 3600  # 1 hour
CACHE_RESPONSE_TTL = 300  # 5 minutes

# Headers
REQUEST_ID_HEADER = "X-Request-ID"
MODEL_NAME_HEADER = "X-Model-Name"
PROVIDER_NAME_HEADER = "X-Provider-Name"
TOKEN_COUNT_HEADER = "X-Token-Count"
PROCESSING_TIME_HEADER = "X-Processing-Time"

# Metrics names
METRIC_REQUEST_DURATION = "request_duration_seconds"
METRIC_REQUEST_COUNT = "request_count"
METRIC_TOKEN_COUNT = "token_count"
METRIC_ERROR_COUNT = "error_count" 