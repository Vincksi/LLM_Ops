import os
from typing import Dict, List, Optional, Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

# Configure logging for the config module
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Server Configuration
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    DEBUG: bool = False
    ENV: str = "development"
    
    # Security
    API_KEY_HEADER: str = "X-API-Key"
    AUTH_ENABLED: bool = True
    JWT_SECRET: str = "your_jwt_secret_key"
    API_KEYS: List[str] = Field(default_factory=lambda: ["key1"])
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_MAX_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # Caching
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 300
    REDIS_URL: Optional[str] = None
    
    # Providers
    DEFAULT_PROVIDER: str = "ollama"
    FALLBACK_PROVIDERS: List[str] = Field(default_factory=lambda: ["ollama"])
    PROVIDER_MODEL_MAPPING: Dict[str, List[str]] = Field(default_factory=dict)
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_TIMEOUT: int = 30
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Process comma-separated environment variables
        if isinstance(self.API_KEYS, str):
            self.API_KEYS = self.API_KEYS.split(",")
        if isinstance(self.FALLBACK_PROVIDERS, str):
            self.FALLBACK_PROVIDERS = self.FALLBACK_PROVIDERS.split(",")
        
        # Process provider model mapping from environment
        if isinstance(self.PROVIDER_MODEL_MAPPING, str):
            try:
                import json
                self.PROVIDER_MODEL_MAPPING = json.loads(self.PROVIDER_MODEL_MAPPING)
            except Exception as e:
                logger.error(f"Error parsing PROVIDER_MODEL_MAPPING: {e}")
                self.PROVIDER_MODEL_MAPPING = {}
        
        # Log loaded settings
        logger.info(f"AUTH_ENABLED: {self.AUTH_ENABLED}")
        logger.info(f"API_KEYS: {self.API_KEYS}")
        logger.info(f"DEFAULT_PROVIDER: {self.DEFAULT_PROVIDER}")

# Create settings instance
settings = Settings()

# Constants
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s" 