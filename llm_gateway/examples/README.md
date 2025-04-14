# Examples

This directory contains examples demonstrating how to use the LLM Gateway's features and modules.

## Available Examples

### Service Factory Example

`service_factory_example.py` demonstrates how to use the Service Factory for provider selection and automatic fallback.

#### Features Demonstrated

- Getting a service for a specific model
- Specifying a preferred provider
- Registering a custom model-provider mapping
- Fallback mechanisms when a provider is unavailable

#### Running the Example

```bash
python -m llm_gateway.examples.service_factory_example
```

#### Key Code Snippets

Selecting a service and running a completion:

```python
# Get a service for the model with optional preferred provider
service = await service_factory.get_service_for_model(model_id, preferred_provider)

# Create a request
request = ChatCompletionRequest(
    model=model_id,
    messages=[
        Message(role="user", content=prompt)
    ]
)

# Run the completion
response = await service.create_chat_completion(request)
```

Registering a custom model-provider mapping:

```python
# Register "custom-model" to be handled by the "ollama" provider
service_factory.register_provider_for_model("custom-model", "ollama")
```

## Creating Your Own Examples

To create your own example:

1. Create a new Python file in this directory
2. Import the necessary modules from LLM Gateway
3. Use the appropriate API methods to demonstrate your use case
4. Add documentation explaining what the example demonstrates

### Template

```python
#!/usr/bin/env python
"""
Example demonstrating [feature description].
"""

import asyncio
import logging
from typing import Optional

from ..services.factory import service_factory
# Import other required modules

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("my_example")

async def main():
    # Your example code here
    pass

if __name__ == "__main__":
    asyncio.run(main())
```

## Best Practices

- Always include proper error handling
- Add informative logging to show what's happening
- Document the purpose of the example at the top of the file
- Create focused examples that demonstrate one feature or concept
- Make examples runnable as standalone scripts 