"""
Configuration settings for JARVIS 3.0 Backend
Centralized configuration management using environment variables
"""

import os
from typing import Optional
from pydantic import BaseModel, field_validator


class Settings(BaseModel):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = os.getenv("APP_NAME", "JARVIS 3.0 Backend")
    version: str = os.getenv("VERSION", "0.1.0")
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/jarvis_db")
    database_echo: bool = os.getenv("DATABASE_ECHO", "False").lower() == "true"
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Supabase
    supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
    supabase_key: Optional[str] = os.getenv("SUPABASE_KEY")
    
    # Vector Database
    vector_dimension: int = int(os.getenv("VECTOR_DIMENSION", "1536"))
    
    # External APIs
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Monitoring
    enable_metrics: bool = os.getenv("ENABLE_METRICS", "True").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # File Processing
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    allowed_file_types: list = os.getenv("ALLOWED_FILE_TYPES", ".txt,.pdf,.docx,.md").split(",")
    
    @field_validator("database_url")
    @classmethod
    def validate_db_connection(cls, v: str) -> str:
        """Ensure database URL is properly formatted"""
        if not v or not isinstance(v, str):
            return "postgresql://postgres:postgres@localhost:5432/jarvis_db"
        return v



# Global settings instance
settings = Settings()


# Configuration for different environments
class DevelopmentSettings(Settings):
    """Development environment settings"""
    debug: bool = True
    database_echo: bool = True
    log_level: str = "DEBUG"


class ProductionSettings(Settings):
    """Production environment settings"""
    debug: bool = False
    database_echo: bool = False
    log_level: str = "WARNING"


class TestingSettings(Settings):
    """Testing environment settings"""
    database_url: str = "postgresql://postgres:postgres@localhost:5432/jarvis_test_db"
    redis_url: str = "redis://localhost:6379/1"
    access_token_expire_minutes: int = 5


def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


# Use environment-specific settings
settings = get_settings()