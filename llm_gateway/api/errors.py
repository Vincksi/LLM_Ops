from fastapi import Request, status
from fastapi.responses import JSONResponse
from ..core.errors import (
    LLMGatewayError,
    InvalidRequestError,
    AuthenticationError,
    AuthorizationError,
    ProviderError,
    RateLimitExceededError,
    ModelNotFoundError,
    ServiceUnavailableError,
    TimeoutError
)
import logging

logger = logging.getLogger("llm_gateway.api.errors")

async def generic_error_handler(request: Request, exc: Exception):
    """Handle any unhandled exceptions."""
    error_id = request.state.request_id if hasattr(request.state, "request_id") else "unknown"
    
    logger.error(f"Unhandled error {error_id}: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected error occurred."
            }
        }
    )

async def gateway_error_handler(request: Request, exc: LLMGatewayError):
    """Handle LLM Gateway specific errors."""
    error_id = request.state.request_id if hasattr(request.state, "request_id") else "unknown"
    
    logger.error(f"Gateway error {error_id}: {exc.error_code} - {exc.error_message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )

def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app."""
    # Register specific error handlers
    app.add_exception_handler(LLMGatewayError, gateway_error_handler)
    app.add_exception_handler(InvalidRequestError, gateway_error_handler)
    app.add_exception_handler(AuthenticationError, gateway_error_handler)
    app.add_exception_handler(AuthorizationError, gateway_error_handler)
    app.add_exception_handler(ProviderError, gateway_error_handler)
    app.add_exception_handler(RateLimitExceededError, gateway_error_handler)
    app.add_exception_handler(ModelNotFoundError, gateway_error_handler)
    app.add_exception_handler(ServiceUnavailableError, gateway_error_handler)
    app.add_exception_handler(TimeoutError, gateway_error_handler)
    
    # Register generic error handler for unhandled exceptions
    app.add_exception_handler(Exception, generic_error_handler) 