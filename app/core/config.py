from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    """Configurações essenciais da aplicação - MVP"""
    
    # App Settings
    APP_NAME: str = Field(default="Conecta+Saúde API", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    APP_DESCRIPTION: str = Field(
        default="API Backend para análise de pacientes com IA",
        env="APP_DESCRIPTION"
    )
    
    # Server Settings
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8082, env="PORT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # API Settings
    API_V1_PREFIX: str = Field(default="/api/v1", env="API_V1_PREFIX")
    DOCS_URL: str = Field(default="/docs", env="DOCS_URL")
    REDOC_URL: str = Field(default="/redoc", env="REDOC_URL")
    
    # CORS Settings
    ALLOWED_ORIGINS: str = Field(
        default="*",
        env="ALLOWED_ORIGINS"
    )
    
    # External APIs
    GEMINI_API_KEY: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    CLASSIFICATION_SERVICE_URL: Optional[str] = Field(default=None, env="CLASSIFICATION_SERVICE_URL")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Optional environment variables that may exist
    ENVIRONMENT: Optional[str] = Field(default="development", env="ENVIRONMENT")
    DATABASE_URL: Optional[str] = Field(default=None, env="DATABASE_URL")
    AWS_REGION: Optional[str] = Field(default=None, env="AWS_REGION")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    HEALTH_CHECK_TIMEOUT: Optional[str] = Field(default="30", env="HEALTH_CHECK_TIMEOUT")
    
    @property
    def cors_origins(self) -> list[str]:
        """Retorna lista de origens CORS permitidas"""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "use_enum_values": True,
        "extra": "ignore"  # Ignora campos extras
    }

# Instância global das configurações
settings = Settings()