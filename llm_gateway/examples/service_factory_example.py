#!/usr/bin/env python
"""
Example demonstrating how to use the ServiceFactory for provider selection and fallback.
"""

import asyncio
import logging
from typing import Optional

from ..services.factory import service_factory
from ..core.models import ChatCompletionRequest, Message
from ..core.errors import ModelNotFoundError, ServiceUnavailableError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("service_factory_example")

async def run_chat_completion(model_id: str, prompt: str, preferred_provider: Optional[str] = None):
    """
    Run a chat completion using the service factory to select the appropriate provider.
    
    Args:
        model_id: The ID of the model to use.
        prompt: The user prompt to send.
        preferred_provider: Optional preferred provider to try first.
    """
    logger.info(f"Running chat completion with model {model_id}")
    
    try:
        # Get a service for the model
        service = await service_factory.get_service_for_model(model_id, preferred_provider)
        logger.info(f"Selected provider: {service.provider_name}")
        
        # Create the request
        request = ChatCompletionRequest(
            model=model_id,
            messages=[
                Message(role="user", content=prompt)
            ]
        )
        
        # Run the completion
        response = await service.create_chat_completion(request)
        
        # Print the response
        logger.info(f"Response from {service.provider_name} using model {model_id}:")
        logger.info(response.choices[0].message.content)
        
        return response
    
    except ModelNotFoundError as e:
        logger.error(f"Model not found: {str(e)}")
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    
    return None

async def main():
    """Main function to run the example."""
    # Example 1: Use the default provider
    await run_chat_completion("llama3.2:1b", "What is the capital of France?")
    
    # Example 2: Try with a preferred provider
    await run_chat_completion(
        "mistral", 
        "Write a short poem about artificial intelligence.",
        preferred_provider="ollama"
    )
    
    # Example 3: Register a custom provider for a model and try using it
    service_factory.register_provider_for_model("custom-model", "ollama")
    await run_chat_completion("custom-model", "Tell me a joke.")

if __name__ == "__main__":
    asyncio.run(main()) 