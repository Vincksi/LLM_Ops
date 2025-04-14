# LLM Gateway

A unified API gateway for LLM providers.

## Quick Start

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r llm_gateway/requirements.txt
   ```
3. Create an `.env` file in the project root to disable authentication:
   ```
   AUTH_ENABLED=false
   ```
   (or provide API keys when making requests)
4. Run the server:
   ```
   python -m llm_gateway.main
   ```

## Architecture

LLM Gateway is built with a modular architecture that enables easy integration of multiple LLM providers:

### Core Components

- **Service Factory**: Centralizes provider management with runtime selection and automatic fallback mechanisms
- **Base Service**: Abstract interface that all provider implementations must follow
- **Provider Services**: Concrete implementations for specific LLM providers (e.g., Ollama)
- **API Layer**: FastAPI endpoints exposing unified endpoints for chat completions, embeddings, etc.

### Module Structure

- `llm_gateway/`
  - `api/`: FastAPI routes and endpoints
  - `core/`: Core functionality, models, error handling
  - `services/`: Service implementations and factory
  - `examples/`: Usage examples

## Service Factory Pattern

The LLM Gateway uses the Factory pattern to create and manage provider services:

```python
from llm_gateway.services import service_factory

# Get the default provider service
service = service_factory.get_service()

# Get service for a specific provider
ollama_service = service_factory.get_service("ollama")

# Get appropriate service for a specific model with provider fallback
service = await service_factory.get_service_for_model("llama3.2:1b")

# Register a provider as compatible with a specific model
service_factory.register_provider_for_model("custom-model", "ollama")
```

### Key Features

- **Runtime Provider Selection**: Automatically selects the appropriate service provider based on the requested model
- **Automatic Fallback**: If a preferred provider is unavailable, falls back to alternative providers
- **Centralized Configuration**: Models and providers are managed in a central location
- **Dynamic Registration**: New providers and model mappings can be registered at runtime

## Service Provider Integration

All service providers implement the `BaseLLMService` interface:

```python
from llm_gateway.services import BaseLLMService

class MyCustomProvider(BaseLLMService):
    # Implementation of required methods
    # ...
```

To add a new provider:

1. Create a new service class that implements `BaseLLMService`
2. Register the service class with the factory:
   ```python
   from llm_gateway.services import service_factory
   service_factory._register_service_class("my_provider", MyCustomProvider)
   ```

## Configuration

The LLM Gateway can be configured through environment variables or the `.env` file in the `llm_gateway` directory. See the example configuration in `llm_gateway/.env.example`.

### Provider Configuration

Configure provider-model mappings:

```
# In .env file
PROVIDER_MODEL_MAPPING={"ollama": ["llama3.2:1b"]}
```

Set default and fallback providers:

```
DEFAULT_PROVIDER=ollama
FALLBACK_PROVIDERS=ollama,another_provider
```

## Authentication

The LLM Gateway supports API key authentication. To use this feature:

1. Set `AUTH_ENABLED=true` in your environment
2. Configure API keys in `llm_gateway/.env` (or use the defaults: key1, key2, key3)
3. Include the API key in your requests with the header `X-API-Key: key1`

To disable authentication, set `AUTH_ENABLED=false` in your environment.

## Examples

Check the `examples` directory for usage examples:

- `service_factory_example.py`: Demonstrates how to use the ServiceFactory for provider selection and fallback

Run an example:

```
python -m llm_gateway.examples.service_factory_example
```

## Docker Deployment

The LLM Gateway can be easily deployed using Docker and Docker Compose.

### Prerequisites

- Docker and Docker Compose installed
- At least 4GB of RAM available for Ollama models

### Deployment Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/llm-gateway.git
   cd llm-gateway
   ```

2. Start the containers:
   ```bash
   docker-compose up -d
   ```

3. Check that the services are running:
   ```bash
   docker-compose ps
   ```

4. Pull a language model in Ollama:
   ```bash
   docker exec ollama ollama pull llama3.2:1b
   ```

5. Access the API at http://localhost:8000

### Docker Services

The Docker Compose setup includes:

- **llm-gateway**: The main service that runs the LLM Gateway API
- **ollama**: Local LLM inference server
- **redis**: Caching and rate limiting

### Environment Configuration

You can customize the docker-compose.yml file to change environment variables:

```yaml
environment:
  - DEBUG=false
  - AUTH_ENABLED=true
  - API_KEYS=key1,key2,key3
  - CACHE_ENABLED=true
  - REDIS_URL=redis://redis:6379/0
  - OLLAMA_BASE_URL=http://ollama:11434
  - DEFAULT_PROVIDER=ollama
  - "PROVIDER_MODEL_MAPPING={\"ollama\": [\"llama3.2:1b\"]}"
```

### Volumes

- **ollama_data**: Persists downloaded models
- **redis_data**: Persists cache data

### Stopping the Services

```bash
docker-compose down
```

To remove all data volumes:
```bash
docker-compose down -v