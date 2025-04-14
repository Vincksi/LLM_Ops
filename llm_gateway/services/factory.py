from typing import Dict, List, Optional, Any, Type
import logging
from abc import ABC
import asyncio

from ..config import settings
from ..core.errors import ModelNotFoundError, ServiceUnavailableError
from .base import BaseLLMService
from .ollama_service import OllamaService
from ..core.utils import get_provider_mapping

logger = logging.getLogger("llm_gateway.services.factory")

class ServiceFactory:
    """
    Factory for LLM services that centralizes provider management,
    enables runtime selection, and implements automatic fallback mechanisms.
    """
    
    _instance = None
    _services: Dict[str, BaseLLMService] = {}
    _service_classes: Dict[str, Type[BaseLLMService]] = {}
    _model_provider_mapping: Dict[str, List[str]] = {}
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super(ServiceFactory, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the factory with available service providers."""
        # Register available service classes
        self._register_service_class("ollama", OllamaService)
        
        # Load model-provider mapping
        self._model_provider_mapping = get_provider_mapping()
    
    def _register_service_class(self, provider_name: str, service_class: Type[BaseLLMService]):
        """Register a service class for a provider."""
        self._service_classes[provider_name.lower()] = service_class
    
    def register_service(self, provider_name: str, service: BaseLLMService):
        """Register an existing service instance."""
        self._services[provider_name.lower()] = service
    
    def get_service(self, provider_name: Optional[str] = None) -> BaseLLMService:
        """
        Get a service instance for the specified provider.
        
        Args:
            provider_name: The name of the provider. If None, the default provider is used.
        
        Returns:
            A service instance for the specified provider.
        
        Raises:
            ServiceUnavailableError: If the provider is not available.
        """
        # If no provider specified, use the default
        if not provider_name:
            provider_name = settings.DEFAULT_PROVIDER
        
        # Normalize provider name
        provider_name = provider_name.lower()
        
        # Check if the service is already instantiated
        if provider_name in self._services:
            return self._services[provider_name]
        
        # Create a new service instance if possible
        if provider_name in self._service_classes:
            service = self._service_classes[provider_name]()
            self._services[provider_name] = service
            return service
        
        # Provider not supported
        raise ServiceUnavailableError(f"Provider '{provider_name}' is not supported")
    
    async def get_service_for_model(
        self, model_id: str, preferred_provider: Optional[str] = None
    ) -> BaseLLMService:
        """
        Get a service that can handle the specified model.
        
        This function will try to find a service that can handle the model,
        first trying the preferred provider, then checking the model-provider mapping,
        then the default provider, and finally any provider that is compatible with the model.
        
        Args:
            model_id: The ID of the model.
            preferred_provider: The preferred provider for this model.
        
        Returns:
            A service that can handle the specified model.
        
        Raises:
            ModelNotFoundError: If no service can handle the model.
            ServiceUnavailableError: If the provider is not available.
        """
        # Try the preferred provider first
        if preferred_provider:
            try:
                service = self.get_service(preferred_provider)
                if await self._is_compatible_with_model(service, model_id):
                    return service
            except ServiceUnavailableError:
                # If the preferred provider is not available, try others
                logger.warning(f"Preferred provider '{preferred_provider}' is not available, trying others")
        
        # Check if we have a mapping for this model
        for provider, models in self._model_provider_mapping.items():
            if model_id in models:
                try:
                    service = self.get_service(provider)
                    if await self._is_compatible_with_model(service, model_id):
                        return service
                except ServiceUnavailableError:
                    logger.warning(f"Mapped provider '{provider}' for model '{model_id}' is not available, trying others")
        
        # Try the default provider
        try:
            service = self.get_service(settings.DEFAULT_PROVIDER)
            if await self._is_compatible_with_model(service, model_id):
                return service
        except ServiceUnavailableError:
            # If the default provider is not available, try others
            logger.warning(f"Default provider '{settings.DEFAULT_PROVIDER}' is not available, trying others")
        
        # Try all providers in the fallback list
        for provider_name in settings.FALLBACK_PROVIDERS:
            try:
                service = self.get_service(provider_name)
                if await self._is_compatible_with_model(service, model_id):
                    return service
            except ServiceUnavailableError:
                continue
        
        # If we reach here, no service can handle the model
        raise ModelNotFoundError(f"No provider available for model '{model_id}'")
    
    async def _is_compatible_with_model(self, service: BaseLLMService, model_id: str) -> bool:
        """Check if a service is compatible with a model using non-blocking methods."""
        # First do a quick check with the synchronous method
        if service.is_compatible_with_model(model_id):
            return True
            
        # If that fails, try to get models asynchronously to confirm
        try:
            models = await service.get_models()
            for model in models:
                if model.id.lower() == model_id.lower():
                    return True
            return False
        except Exception as e:
            logger.warning(f"Error checking model compatibility: {str(e)}")
            return False
    
    async def get_all_services(self) -> List[BaseLLMService]:
        """
        Get all available services.
        
        Returns:
            A list of all available services.
        """
        providers = set([settings.DEFAULT_PROVIDER] + settings.FALLBACK_PROVIDERS)
        services = []
        
        for provider_name in providers:
            try:
                service = self.get_service(provider_name)
                services.append(service)
            except ServiceUnavailableError:
                continue
        
        return services

    def register_provider_for_model(self, model_id: str, provider_name: str):
        """
        Register a provider as compatible with a specific model.
        
        Args:
            model_id: The ID of the model.
            provider_name: The name of the provider.
        """
        provider_name = provider_name.lower()
        if provider_name not in self._model_provider_mapping:
            self._model_provider_mapping[provider_name] = []
        
        if model_id not in self._model_provider_mapping[provider_name]:
            self._model_provider_mapping[provider_name].append(model_id)
    
    def get_provider_for_model(self, model_id: str) -> Optional[str]:
        """
        Get the primary provider for a specific model.
        
        Args:
            model_id: The ID of the model.
        
        Returns:
            The name of the provider, or None if no specific provider is registered.
        """
        for provider, models in self._model_provider_mapping.items():
            if model_id in models:
                return provider
        return None

# Create a singleton instance
service_factory = ServiceFactory() 