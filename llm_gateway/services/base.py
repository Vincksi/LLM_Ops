from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..core.models import (
    ChatCompletionRequest, 
    ChatCompletionResponse,
    EmbeddingRequest, 
    EmbeddingResponse,
    ModelInfo
)

class BaseLLMService(ABC):
    """Base class for all LLM service providers."""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the name of the provider."""
        pass
    
    @abstractmethod
    async def get_models(self) -> List[ModelInfo]:
        """Get a list of available models."""
        pass
    
    @abstractmethod
    async def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get information about a specific model."""
        pass
    
    @abstractmethod
    async def create_chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Create a chat completion."""
        pass
    
    @abstractmethod
    async def create_embeddings(
        self, request: EmbeddingRequest
    ) -> EmbeddingResponse:
        """Create embeddings for the given text."""
        pass
    
    @abstractmethod
    async def check_health(self) -> bool:
        """Check if the service is healthy."""
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """Count the number of tokens in the text for the given model."""
        pass
    
    @abstractmethod
    def format_prompt(
        self, messages: List[Dict[str, Any]], model: str
    ) -> str:
        """Format chat messages into a prompt string for the specified model."""
        pass

    def is_compatible_with_model(self, model_id: str) -> bool:
        """Check if this service is compatible with the given model."""
        # Si le modèle commence par le nom du fournisseur, on le considère comme compatible
        if model_id.lower().startswith(self.provider_name.lower()):
            return True
        
        # Sinon on vérifie si ce modèle est disponible dans le fournisseur
        try:
            import asyncio
            models = asyncio.run(self.get_models())
            for model in models:
                if model.id.lower() == model_id.lower():
                    return True
            return False
        except:
            # En cas d'erreur, on utilise la méthode simple
            return model_id.lower() == self.provider_name.lower() 