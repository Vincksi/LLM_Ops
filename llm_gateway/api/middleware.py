import time
import logging
from typing import Callable, Dict, List
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from prometheus_client import Counter, Histogram
import uuid

from ..config import settings
from ..core.errors import (
    AuthenticationError,
    RateLimitExceededError
)
from ..core.utils import (
    generate_request_id,
    get_client_ip,
    is_rate_limited
)
from ..core.constants import (
    REQUEST_ID_HEADER,
    PROCESSING_TIME_HEADER,
    METRIC_REQUEST_COUNT,
    METRIC_REQUEST_DURATION,
    METRIC_ERROR_COUNT
)

logger = logging.getLogger("llm_gateway.api.middleware")

# Initialize metrics
REQUEST_COUNT = Counter(
    METRIC_REQUEST_COUNT,
    "Count of requests received",
    ["method", "endpoint", "status"]
)

REQUEST_DURATION = Histogram(
    METRIC_REQUEST_DURATION,
    "Histogram of request processing time (seconds)",
    ["method", "endpoint"]
)

ERROR_COUNT = Counter(
    METRIC_ERROR_COUNT,
    "Count of errors",
    ["method", "endpoint", "error_type"]
)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and log information."""
        # Generate a unique request ID
        request_id = generate_request_id()
        request.state.request_id = request_id
        
        # Get client IP
        client_ip = get_client_ip(request)
        
        # Add request ID header to the response
        start_time = time.time()
        
        try:
            # Log request
            logger.info(f"Request {request_id} | {request.method} {request.url.path} | Client: {client_ip}")
            
            # Process the request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            duration_ms = duration * 1000
            
            # Add custom headers
            response.headers[REQUEST_ID_HEADER] = request_id
            response.headers[PROCESSING_TIME_HEADER] = f"{duration_ms:.2f}ms"
            
            # Log response
            logger.info(f"Response {request_id} | Status: {response.status_code} | Duration: {duration_ms:.2f}ms")
            
            # Update metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            return response
        except Exception as e:
            # Log error
            logger.error(f"Error {request_id} | {type(e).__name__}: {str(e)}")
            
            # Update error metrics
            ERROR_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                error_type=type(e).__name__
            ).inc()
            
            # Re-raise the exception
            raise

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication."""
    
    def __init__(self, app: ASGIApp, excluded_paths: List[str] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
        self.auth_enabled = settings.AUTH_ENABLED
        self.api_key_header = settings.API_KEY_HEADER
        self.api_keys = settings.API_KEYS
    
    async def dispatch(self, request: Request, call_next):
        """Authenticate requests using API keys."""
        # Skip authentication for excluded paths or if auth is disabled
        if not self.auth_enabled or any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Check for API key
        api_key = request.headers.get(self.api_key_header)
        if not api_key:
            raise AuthenticationError("Missing API key")
        
        # Validate API key
        if api_key not in self.api_keys:
            raise AuthenticationError("Invalid API key")
        
        # Store API key for rate limiting
        request.state.api_key = api_key
        
        return await call_next(request)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""
    
    def __init__(self, app: ASGIApp, excluded_paths: List[str] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
        self.rate_limit_enabled = settings.RATE_LIMIT_ENABLED
        self.max_requests = settings.RATE_LIMIT_MAX_REQUESTS
        self.window_seconds = settings.RATE_LIMIT_WINDOW_SECONDS
    
    async def dispatch(self, request: Request, call_next):
        """Rate limit requests based on API key or client IP."""
        # Skip rate limiting for excluded paths
        if not self.rate_limit_enabled or any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Get the rate limit key (API key or client IP)
        rate_limit_key = getattr(request.state, "api_key", None) or get_client_ip(request)
        
        # Check rate limit
        if is_rate_limited(rate_limit_key, self.max_requests, self.window_seconds):
            raise RateLimitExceededError(
                f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_seconds} seconds."
            )
        
        return await call_next(request)

def register_middleware(app):
    """Register all middleware with the FastAPI app."""
    # Register middleware in reverse order (last registered is executed first)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AuthenticationMiddleware) 