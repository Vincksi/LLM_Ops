from typing import Dict, Optional, List
from fastapi import Depends, Request
import logging
from ..config import settings
from ..core.errors import (
    ModelNotFoundError,
    ServiceUnavailableError
)
from ..services.base import BaseLLMService
from ..services.factory import service_factory

logger = logging.getLogger("llm_gateway.api.dependencies")

def get_service(provider_name: Optional[str] = None) -> BaseLLMService:
    """
    Get a service instance for the specified provider.
    
    Args:
        provider_name: The name of the provider. If None, the default provider is used.
    
    Returns:
        A service instance for the specified provider.
    
    Raises:
        ServiceUnavailableError: If the provider is not available.
    """
    return service_factory.get_service(provider_name)

async def get_service_for_model(
    model_id: str, 
    preferred_provider: Optional[str] = None
) -> BaseLLMService:
    """
    Get a service that can handle the specified model.
    
    This function will try to find a service that can handle the model,
    first trying the preferred provider, then the default provider,
    and finally any provider that is compatible with the model.
    
    Args:
        model_id: The ID of the model.
        preferred_provider: The preferred provider for this model.
    
    Returns:
        A service that can handle the specified model.
    
    Raises:
        ModelNotFoundError: If no service can handle the model.
        ServiceUnavailableError: If the provider is not available.
    """
    return await service_factory.get_service_for_model(model_id, preferred_provider)

async def get_all_services() -> List[BaseLLMService]:
    """
    Get all available services.
    
    Returns:
        A list of all available services.
    """
    return await service_factory.get_all_services()

def get_request_id(request: Request) -> str:
    """
    Get the request ID from the request state.
    
    Args:
        request: The FastAPI request object.
        
    Returns:
        The request ID as a string.
    """
    return getattr(request.state, "request_id", "unknown") 