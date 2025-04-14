# Core Module

This module contains the core functionality, models, constants, error handling, and utilities used throughout the LLM Gateway.

## Components

### Models (`models.py`)

Defines the data models used for requests and responses:

- `ChatCompletionRequest`: Model for chat completion requests
- `ChatCompletionResponse`: Model for chat completion responses
- `EmbeddingRequest`: Model for embedding requests
- `EmbeddingResponse`: Model for embedding responses
- `ModelInfo`: Information about an LLM model
- `Message`: Chat message structure
- `Usage`: Token usage tracking

### Errors (`errors.py`)

Defines custom exceptions used throughout the application:

- `BaseError`: Base class for all custom errors
- `ProviderError`: Errors from the LLM provider
- `ModelNotFoundError`: When a requested model is not found
- `ServiceUnavailableError`: When a service is not available
- `InvalidRequestError`: When a request is invalid
- `AuthenticationError`: For authentication failures
- `RateLimitError`: When rate limits are exceeded
- `TimeoutError`: When a request times out

### Constants (`constants.py`)

Defines constants used throughout the application:

- `ModelCapability`: Enum of model capabilities (CHAT, EMBEDDING, etc.)
- `CACHE_KEY_PREFIX`: Prefix for cache keys
- Various other constants related to timeouts, rate limits, etc.

### Utilities (`utils.py`)

Provides common utility functions:

#### Caching

- `cache_get`: Get a value from the cache
- `cache_set`: Set a value in the cache
- `calculate_hash`: Generate a hash for cache keys

#### Provider Mapping

- `get_provider_mapping`: Get mappings of models to providers
- `get_compatible_providers`: Find providers compatible with a model

#### Logging and Monitoring

- `log_request`: Log information about requests
- `log_response`: Log information about responses
- `log_error`: Log detailed error information

#### Request Handling

- `generate_request_id`: Generate a unique ID for each request
- `get_timestamp`: Get the current time in ISO format
- `get_client_ip`: Extract client IP from a request
- `is_rate_limited`: Check if a request is rate limited

## Usage

### Provider Mapping

```python
from llm_gateway.core.utils import get_provider_mapping, get_compatible_providers

# Get all provider mappings
mappings = get_provider_mapping()
# Returns: {"ollama": ["llama3.2:1b", "llama2", ...]}

# Find providers for a specific model
providers = get_compatible_providers("llama3.2:1b")
# Returns: ["ollama"]
```

### Caching

```python
from llm_gateway.core.utils import cache_get, cache_set

# Cache a value
await cache_set("key", {"data": "value"}, ttl=300)

# Retrieve a cached value
value = await cache_get("key")
```

### Error Handling

```python
from llm_gateway.core.errors import ModelNotFoundError, ServiceUnavailableError

try:
    # Some operation
    pass
except ModelNotFoundError as e:
    # Handle model not found
    pass
except ServiceUnavailableError as e:
    # Handle service unavailable
    pass
```

## Extending

### Adding New Utilities

Add new utility functions to `utils.py` for functionality used across multiple modules.

### Adding New Models

Add new data models to `models.py` when introducing new request or response types.

### Adding New Errors

Add new exception classes to `errors.py` when introducing new error conditions. 