from typing import Any, Dict, Optional
from fastapi import status
from .constants import ErrorCode

class LLMGatewayError(Exception):
    """Base exception for all LLM Gateway errors."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = ErrorCode.INTERNAL_SERVER_ERROR
    error_message: str = "An unexpected error occurred"
    
    def __init__(
        self, 
        message: Optional[str] = None, 
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_message = message or self.error_message
        self.status_code = status_code or self.status_code
        self.error_code = error_code or self.error_code
        self.details = details or {}
        super().__init__(self.error_message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary for API responses."""
        error_dict = {
            "error": {
                "code": self.error_code,
                "message": self.error_message,
            }
        }
        if self.details:
            error_dict["error"]["details"] = self.details
        return error_dict

class InvalidRequestError(LLMGatewayError):
    """Exception for invalid request errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = ErrorCode.INVALID_REQUEST
    error_message = "Invalid request parameters"

class AuthenticationError(LLMGatewayError):
    """Exception for authentication errors."""
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = ErrorCode.AUTHENTICATION_ERROR
    error_message = "Authentication failed"

class AuthorizationError(LLMGatewayError):
    """Exception for authorization errors."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = ErrorCode.AUTHORIZATION_ERROR
    error_message = "Not authorized to access this resource"

class ProviderError(LLMGatewayError):
    """Exception for provider-specific errors."""
    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = ErrorCode.PROVIDER_ERROR
    error_message = "Error from LLM provider"

class RateLimitExceededError(LLMGatewayError):
    """Exception for rate limit exceeded errors."""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = ErrorCode.RATE_LIMIT_EXCEEDED
    error_message = "Rate limit exceeded"

class ModelNotFoundError(LLMGatewayError):
    """Exception for model not found errors."""
    status_code = status.HTTP_404_NOT_FOUND
    error_code = ErrorCode.MODEL_NOT_FOUND
    error_message = "Requested model not found"

class ServiceUnavailableError(LLMGatewayError):
    """Exception for service unavailable errors."""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = ErrorCode.SERVICE_UNAVAILABLE
    error_message = "Service is currently unavailable"

class TimeoutError(LLMGatewayError):
    """Exception for timeout errors."""
    status_code = status.HTTP_504_GATEWAY_TIMEOUT
    error_code = ErrorCode.TIMEOUT_ERROR
    error_message = "Request timed out" 