import json
import time
import httpx
from typing import Any, Dict, List, Optional, Union
import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from ..config import settings
from .base import BaseLLMService
from ..core.models import (
    ChatCompletionRequest, 
    ChatCompletionResponse,
    EmbeddingRequest, 
    EmbeddingResponse,
    ModelInfo,
    Message,
    Usage,
    ChatCompletionChoice,
    EmbeddingData
)
from ..core.errors import (
    ProviderError,
    ModelNotFoundError,
    ServiceUnavailableError,
    TimeoutError as GatewayTimeoutError
)
from ..core.constants import ModelCapability

logger = logging.getLogger("llm_gateway.ollama")

class OllamaService(BaseLLMService):
    """Implementation of the Ollama LLM service."""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.timeout = settings.OLLAMA_TIMEOUT
        
    @property
    def provider_name(self) -> str:
        return "ollama"
        
    async def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a request to the Ollama API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.lower() == "get":
                    response = await client.get(url)
                elif method.lower() == "post":
                    response = await client.post(url, json=data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as e:
            logger.error(f"Timeout error connecting to Ollama: {str(e)}")
            raise GatewayTimeoutError(f"Request to Ollama timed out: {str(e)}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Ollama: {str(e)}")
            if e.response.status_code == 404:
                raise ModelNotFoundError(f"Model not found: {str(e)}")
            else:
                raise ProviderError(f"Error from Ollama API: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"Error connecting to Ollama: {str(e)}")
            raise ServiceUnavailableError(f"Ollama service unavailable: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(ServiceUnavailableError)
    )
    async def get_models(self) -> List[ModelInfo]:
        """Get a list of available models from Ollama."""
        try:
            response = await self._make_request("GET", "/api/tags")
            models = []
            
            for model_data in response.get("models", []):
                name = model_data.get("name", "")
                models.append(ModelInfo(
                    id=name,
                    name=name,
                    provider=self.provider_name,
                    capabilities=[
                        ModelCapability.CHAT,
                        ModelCapability.EMBEDDING
                    ],
                    max_tokens=4096,  # Default for most Ollama models
                    description=f"Ollama model: {name}",
                    context_window=4096  # Default for most Ollama models
                ))
            
            # Si aucun modèle n'est trouvé, fournir une liste par défaut
            if not models:
                default_model_names = ["llama2", "mistral", "codellama", "phi", "gemma", "llama3.2:1b"]
                for name in default_model_names:
                    models.append(ModelInfo(
                        id=name,
                        name=name,
                        provider=self.provider_name,
                        capabilities=[
                            ModelCapability.CHAT,
                            ModelCapability.EMBEDDING
                        ],
                        max_tokens=4096,
                        description=f"Ollama model: {name}",
                        context_window=4096
                    ))
            
            return models
        except Exception as e:
            logger.warning(f"Error getting models from Ollama: {str(e)}, returning default models")
            # En cas d'erreur, retourner une liste par défaut de modèles
            default_model_names = ["llama2", "mistral", "codellama", "phi", "gemma", "llama3.2:1b"]
            models = []
            for name in default_model_names:
                models.append(ModelInfo(
                    id=name,
                    name=name,
                    provider=self.provider_name,
                    capabilities=[
                        ModelCapability.CHAT,
                        ModelCapability.EMBEDDING
                    ],
                    max_tokens=4096,
                    description=f"Ollama model: {name}",
                    context_window=4096
                ))
            return models
    
    async def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get information about a specific model from Ollama."""
        models = await self.get_models()
        for model in models:
            if model.id.lower() == model_id.lower():
                return model
        return None
    
    async def create_chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Create a chat completion using Ollama."""
        try:
            # Extract request parameters
            model = request.model
            messages = request.messages
            temperature = request.temperature
            top_p = request.top_p
            max_tokens = request.max_tokens
            stop = request.stop
            
            # Format messages for Ollama
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Prepare the request data
            data = {
                "model": model,
                "messages": formatted_messages,
                "options": {
                    "temperature": temperature,
                    "top_p": top_p,
                }
            }
            
            if max_tokens:
                data["options"]["num_predict"] = max_tokens
                
            if stop:
                if isinstance(stop, str):
                    data["options"]["stop"] = [stop]
                else:
                    data["options"]["stop"] = stop
            
            # Make the request to Ollama
            start_time = time.time()
            response = await self._make_request("POST", "/api/chat", data)
            end_time = time.time()
            
            # Extract response
            assistant_message = response.get("message", {})
            content = assistant_message.get("content", "")
            
            # Create the response
            completion = ChatCompletionResponse(
                id=f"ollama-{int(time.time())}",
                object="chat.completion",
                created=int(time.time()),
                model=model,
                provider=self.provider_name,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=Message(
                            role="assistant",
                            content=content
                        ),
                        finish_reason="stop"
                    )
                ],
                usage=Usage(
                    prompt_tokens=response.get("prompt_eval_count", 0),
                    completion_tokens=response.get("eval_count", 0),
                    total_tokens=response.get("prompt_eval_count", 0) + response.get("eval_count", 0)
                )
            )
            
            return completion
        except Exception as e:
            logger.error(f"Error creating chat completion with Ollama: {str(e)}")
            if isinstance(e, (ModelNotFoundError, ProviderError, ServiceUnavailableError, GatewayTimeoutError)):
                raise
            raise ProviderError(f"Failed to create chat completion with Ollama: {str(e)}")
    
    async def create_embeddings(
        self, request: EmbeddingRequest
    ) -> EmbeddingResponse:
        """Create embeddings for the given text using Ollama."""
        try:
            model = request.model
            input_text = request.input
            
            # Convert input to list if it's a string
            if isinstance(input_text, str):
                input_texts = [input_text]
            else:
                input_texts = input_text
            
            embeddings = []
            total_tokens = 0
            
            # Process each text and get embedding
            for i, text in enumerate(input_texts):
                data = {
                    "model": model,
                    "prompt": text
                }
                
                response = await self._make_request("POST", "/api/embeddings", data)
                
                # Extract embedding
                embedding = response.get("embedding", [])
                tokens = response.get("token_count", 0)
                total_tokens += tokens
                
                embeddings.append(
                    EmbeddingData(
                        index=i,
                        embedding=embedding,
                        object="embedding"
                    )
                )
            
            # Create the response
            embedding_response = EmbeddingResponse(
                object="list",
                data=embeddings,
                model=model,
                provider=self.provider_name,
                usage=Usage(
                    prompt_tokens=total_tokens,
                    completion_tokens=0,
                    total_tokens=total_tokens
                )
            )
            
            return embedding_response
        except Exception as e:
            logger.error(f"Error creating embeddings with Ollama: {str(e)}")
            if isinstance(e, (ModelNotFoundError, ProviderError, ServiceUnavailableError, GatewayTimeoutError)):
                raise
            raise ProviderError(f"Failed to create embeddings with Ollama: {str(e)}")
    
    async def check_health(self) -> bool:
        """Check if Ollama is healthy."""
        try:
            # Simple health check by getting the list of models
            await self._make_request("GET", "/api/tags")
            return True
        except Exception:
            return False
    
    async def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count the number of tokens in the text for the given model.
        Note: This is a rough estimate as Ollama doesn't provide a dedicated tokenization endpoint.
        """
        try:
            # Use a simple approximation
            return len(text.split()) * 4 // 3  # Rough estimate: 4 tokens for every 3 words
        except Exception as e:
            logger.error(f"Error counting tokens: {str(e)}")
            return len(text.split())
    
    def format_prompt(
        self, messages: List[Dict[str, Any]], model: str
    ) -> str:
        """Format chat messages into a prompt string for the specified model."""
        prompt = ""
        for message in messages:
            role = message.get("role", "").lower()
            content = message.get("content", "")
            
            if role == "system":
                prompt += f"<system>\n{content}\n</system>\n\n"
            elif role == "user":
                prompt += f"<human>\n{content}\n</human>\n\n"
            elif role == "assistant":
                prompt += f"<assistant>\n{content}\n</assistant>\n\n"
        
        # Add final assistant prompt
        prompt += "<assistant>\n"
        
        return prompt 
    
    def is_compatible_with_model(self, model_id: str) -> bool:
        """Check if this service is compatible with the given model."""
        # Si le modèle est llama3.2:1b, on le considère toujours compatible avec Ollama
        if model_id.lower() == "llama3.2:1b":
            logger.info(f"Model {model_id} is explicitly supported by {self.provider_name}")
            return True
            
        # Si le modèle commence par le nom du fournisseur, on le considère comme compatible
        if model_id.lower().startswith(self.provider_name.lower()):
            return True
        
        # Pour les autres modèles, on vérifie dans la liste
        default_model_names = ["llama2", "mistral", "codellama", "phi", "gemma", "llama3.2:1b"]
        if model_id.lower() in [name.lower() for name in default_model_names]:
            logger.info(f"Model {model_id} is in the default supported models for {self.provider_name}")
            return True
        
        # En dernier recours, on essaie de récupérer la liste des modèles
        try:
            import asyncio
            models = asyncio.run(self.get_models())
            for model in models:
                if model.id.lower() == model_id.lower():
                    return True
            return False
        except Exception as e:
            logger.warning(f"Error checking model compatibility: {str(e)}")
            return False 