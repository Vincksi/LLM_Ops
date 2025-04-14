from fastapi import APIRouter, Depends, Request, HTTPException, status
from typing import Optional
import time
import logging

from ...core.models import EmbeddingRequest, EmbeddingResponse
from ...core.errors import ModelNotFoundError, ServiceUnavailableError, ProviderError
from ...core.utils import create_cache_key, cache_get, cache_set
from ...config import settings
from ..dependencies import get_service_for_model, get_request_id

logger = logging.getLogger("llm_gateway.api.routers.embeddings")

router = APIRouter(prefix="/v1", tags=["Embeddings"])

@router.post("/embeddings", response_model=EmbeddingResponse)
async def create_embeddings(
    request: Request,
    body: EmbeddingRequest,
    request_id: str = Depends(get_request_id)
):
    """
    Create embeddings for the given input.
    
    This endpoint creates embeddings for the given text and model.
    It supports the same parameters as the OpenAI Embeddings API, but with the
    addition of a 'provider' parameter to specify which provider to use.
    """
    start_time = time.time()
    
    model = body.model
    provider = body.provider
    
    logger.info(f"Request {request_id} | Embeddings with model '{model}' and provider '{provider or 'default'}'")
    
    # Try to get from cache if caching is enabled
    if settings.CACHE_ENABLED:
        cache_key = create_cache_key("embedding", body.dict())
        cached_response = await cache_get(cache_key)
        if cached_response:
            logger.info(f"Request {request_id} | Cache hit for model '{model}'")
            return EmbeddingResponse(**cached_response)
    
    try:
        # Get the appropriate service for this model
        service = await get_service_for_model(model, provider)
        
        # Create the embeddings
        response = await service.create_embeddings(body)
        
        # Store in cache if needed
        if settings.CACHE_ENABLED:
            await cache_set(create_cache_key("embedding", body.dict()), response.dict())
        
        duration = time.time() - start_time
        logger.info(f"Request {request_id} | Completed in {duration:.2f}s")
        
        return response
    except ModelNotFoundError as e:
        logger.error(f"Request {request_id} | Model not found: {model}")
        raise e
    except ServiceUnavailableError as e:
        logger.error(f"Request {request_id} | Service unavailable for provider: {provider}")
        raise e
    except ProviderError as e:
        logger.error(f"Request {request_id} | Provider error: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Request {request_id} | Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )