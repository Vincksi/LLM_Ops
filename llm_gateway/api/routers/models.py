from fastapi import APIRouter, Depends, Request, HTTPException, status, Query
from typing import Optional, List
import time
import logging

from ...core.models import ModelInfo, ModelListResponse
from ...core.errors import ServiceUnavailableError, ModelNotFoundError
from ...core.constants import ModelCapability
from ...core.utils import create_cache_key, cache_get, cache_set
from ...config import settings
from ..dependencies import get_service, get_all_services, get_request_id

logger = logging.getLogger("llm_gateway.api.routers.models")

router = APIRouter(prefix="/v1", tags=["Models"])

@router.get("/models", response_model=ModelListResponse)
async def list_models(
    request: Request,
    provider: Optional[str] = Query(None, description="Filter models by provider"),
    capability: Optional[str] = Query(None, description="Filter models by capability (chat, embedding, completion)"),
    request_id: str = Depends(get_request_id)
):
    """
    List available models.
    
    This endpoint lists all available models across all providers,
    with optional filtering by provider and capability.
    """
    start_time = time.time()
    
    logger.info(f"Request {request_id} | List models (provider: {provider or 'all'}, capability: {capability or 'all'})")
    
    # Try to get from cache if caching is enabled
    cache_key = None
    if settings.CACHE_ENABLED:
        cache_params = {"provider": provider, "capability": capability}
        cache_key = create_cache_key("models", cache_params)
        cached_response = await cache_get(cache_key)
        if cached_response:
            logger.info(f"Request {request_id} | Cache hit for models list")
            return ModelListResponse(**cached_response)
    
    try:
        models = []
        
        if provider:
            # Get models from a specific provider
            service = get_service(provider)
            provider_models = await service.get_models()
            models.extend(provider_models)
        else:
            # Get models from all available providers
            services = await get_all_services()
            for service in services:
                try:
                    provider_models = await service.get_models()
                    models.extend(provider_models)
                except Exception as e:
                    logger.warning(f"Failed to get models from provider {service.provider_name}: {str(e)}")
        
        # Filter by capability if specified
        if capability:
            capability = capability.lower()
            models = [m for m in models if capability in [c.lower() for c in m.capabilities]]
        
        # Create the response
        response = ModelListResponse(
            object="list",
            data=models
        )
        
        # Store in cache if needed
        if settings.CACHE_ENABLED and cache_key:
            await cache_set(cache_key, response.dict(), ttl=300)  # Cache for 5 minutes
        
        duration = time.time() - start_time
        logger.info(f"Request {request_id} | Completed in {duration:.2f}s, found {len(models)} models")
        
        return response
    except ServiceUnavailableError as e:
        logger.error(f"Request {request_id} | Service unavailable: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Request {request_id} | Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

@router.get("/models/{model_id}", response_model=ModelInfo)
async def get_model(
    request: Request,
    model_id: str,
    provider: Optional[str] = Query(None, description="The provider to use for this model"),
    request_id: str = Depends(get_request_id)
):
    """
    Get information about a specific model.
    
    This endpoint returns detailed information about a specific model,
    optionally from a specific provider.
    """
    start_time = time.time()
    
    logger.info(f"Request {request_id} | Get model '{model_id}' (provider: {provider or 'default'})")
    
    # Try to get from cache if caching is enabled
    cache_key = None
    if settings.CACHE_ENABLED:
        cache_params = {"model_id": model_id, "provider": provider}
        cache_key = create_cache_key("model", cache_params)
        cached_response = await cache_get(cache_key)
        if cached_response:
            logger.info(f"Request {request_id} | Cache hit for model '{model_id}'")
            return ModelInfo(**cached_response)
    
    try:
        # If provider is specified, use that provider
        if provider:
            service = get_service(provider)
            model_info = await service.get_model_info(model_id)
            if not model_info:
                raise ModelNotFoundError(f"Model '{model_id}' not found for provider '{provider}'")
        else:
            # Try to find the model across all providers
            services = await get_all_services()
            model_info = None
            
            for service in services:
                try:
                    info = await service.get_model_info(model_id)
                    if info:
                        model_info = info
                        break
                except Exception:
                    continue
            
            if not model_info:
                raise ModelNotFoundError(f"Model '{model_id}' not found")
        
        # Store in cache if needed
        if settings.CACHE_ENABLED and cache_key:
            await cache_set(cache_key, model_info.dict(), ttl=300)  # Cache for 5 minutes
        
        duration = time.time() - start_time
        logger.info(f"Request {request_id} | Completed in {duration:.2f}s")
        
        return model_info
    except ModelNotFoundError as e:
        logger.error(f"Request {request_id} | Model not found: {model_id}")
        raise e
    except ServiceUnavailableError as e:
        logger.error(f"Request {request_id} | Service unavailable: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Request {request_id} | Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        ) 