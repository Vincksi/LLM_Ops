# Services Module

This module manages the various LLM service providers and implements the Service Factory pattern.

## Structure

- `base.py`: Abstract base class defining the interface for all LLM services
- `ollama_service.py`: Implementation for the Ollama LLM provider
- `factory.py`: Service Factory implementation with singleton pattern and provider registration
- `__init__.py`: Package exports

## Service Factory

The Service Factory implements the Factory design pattern to centralize provider management, enable runtime selection, and implement automatic fallback mechanisms.

### Key Features

1. **Singleton Pattern**: Ensures there's only one factory instance throughout the application
2. **Provider Management**: Centralized registration and access to service providers
3. **Runtime Selection**: Dynamically selects the appropriate provider based on the requested model
4. **Automatic Fallback**: If a preferred provider is unavailable, tries alternative providers
5. **Model-Provider Mapping**: Maintains a mapping of models to compatible providers

### Using the Factory

```python
from llm_gateway.services.factory import service_factory

# Basic usage
service = service_factory.get_service("ollama")
service = service_factory.get_service()  # Uses DEFAULT_PROVIDER

# Model-based selection with fallback
service = await service_factory.get_service_for_model("llama3.2:1b")
service = await service_factory.get_service_for_model("mistral", preferred_provider="ollama")

# Registration
service_factory.register_provider_for_model("my-custom-model", "ollama")
```

### Adding a New Provider

1. Create a new provider class that implements `BaseLLMService`
2. Register the provider class with the factory

```python
class MyCustomProvider(BaseLLMService):
    # Implement required methods
    ...

# Register during initialization
service_factory._register_service_class("my_provider", MyCustomProvider)

# Or register an existing instance
service = MyCustomProvider()
service_factory.register_service("my_provider", service)
```

## Model-Provider Mapping

The factory uses a mapping to determine which providers can handle which models. This mapping can be:

1. **Hardcoded**: Default mappings in `core/utils.py`
2. **Environment-based**: Set via `PROVIDER_MODEL_MAPPING` in `.env`
3. **Runtime-registered**: Added during execution via `register_provider_for_model`

### Configuration

In `.env` file:
```
PROVIDER_MODEL_MAPPING={"ollama": ["llama3.2:1b", "llama2", "mistral"]}
```

## Fallback Mechanisms

If a model can't be handled by the preferred provider, the factory follows this fallback sequence:

1. Try the preferred provider (if specified)
2. Check the model-provider mapping for compatible providers
3. Try the default provider
4. Try all providers in the fallback list

This ensures the highest chance of serving the request, even if some providers are unavailable.

## Error Handling

The factory handles these error conditions:

- `ServiceUnavailableError`: When a provider is not available
- `ModelNotFoundError`: When no provider can handle the requested model

## Example Usage

See `examples/service_factory_example.py` for a comprehensive example of using the Service Factory. 