"""Configuration management for Business Assistant.

Supports environment-specific settings, validation, and secure defaults.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Literal
from dotenv import load_dotenv

try:
    from pydantic_settings import BaseSettings  # pydantic v2 (separate package)
    from pydantic import Field, validator
except Exception:
    from pydantic import BaseSettings, Field, validator  # fallback for pydantic v1

# Load environment variables from .env file
load_dotenv()

# Determine environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()


class Settings(BaseSettings):
    """
    Application-wide settings and configuration with validation.
    
    Supports environment-specific configurations via ENVIRONMENT variable.
    Valid values: development, staging, production
    """

    # Environment
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment"
    )

    # Base paths
    BASE_DIR: Path = Path(__file__).parent.parent.absolute()
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = BASE_DIR / "logs"
    EXPORTS_DIR: Path = BASE_DIR / "exports"
    CACHE_DIR: Path = BASE_DIR / "cache"

    # File paths
    LOG_FILE: str = str(LOGS_DIR / "qa_log.txt")
    DB_PATH: str = str(BASE_DIR / "business_assistant.db")

    # Vector DB paths for policy embeddings
    VECTOR_STORE_PATH: str = str(BASE_DIR / "vector_store")

    # Text splitting settings
    CHUNK_SIZE: int = Field(default=500, ge=100, le=2000, description="Text chunk size for embeddings")
    CHUNK_OVERLAP: int = Field(default=100, ge=0, le=500, description="Overlap between chunks")

    # Model settings
    LLM_MODEL: str = Field(default="gemma2-9b-it", description="Groq LLM model name")
    TEMPERATURE: float = Field(default=0.3, ge=0.0, le=2.0, description="LLM temperature")
    MAX_TOKENS: int = Field(default=2048, ge=100, le=8192, description="Max tokens per response")

    # Retrieval settings
    TOP_K_MATCHES: int = Field(default=3, ge=1, le=20, description="Number of policy matches to retrieve")
    SIMILARITY_THRESHOLD: float = Field(default=-1.0, ge=-1.0, le=1.0, description="Minimum similarity score")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    ENABLE_DEBUG: bool = Field(default=True, description="Enable debug mode")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )

    # API keys
    GROQ_API_KEY: Optional[str] = Field(default=None, description="Groq API key")

    # Security settings
    SECRET_KEY: str = Field(
        default_factory=lambda: os.urandom(32).hex(),
        description="Secret key for session management"
    )
    ALLOWED_HOSTS: str = Field(
        default="127.0.0.1,localhost",
        description="Comma-separated list of allowed hosts"
    )
    ENABLE_AUTH: bool = Field(default=False, description="Enable authentication")
    SESSION_TIMEOUT: int = Field(default=3600, description="Session timeout in seconds")

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Requests per window")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="Rate limit window in seconds")

    # Caching
    CACHE_ENABLED: bool = Field(default=True, description="Enable response caching")
    CACHE_TTL: int = Field(default=3600, description="Cache TTL in seconds")
    CACHE_MAX_SIZE: int = Field(default=1000, description="Maximum cache entries")

    # File upload settings
    MAX_UPLOAD_SIZE: int = Field(default=50 * 1024 * 1024, description="Max upload size in bytes (50MB)")
    ALLOWED_EXTENSIONS: str = Field(
        default="csv,xlsx,xls,json,txt,pdf",
        description="Comma-separated allowed file extensions"
    )

    # Database settings
    DB_TYPE: Literal["sqlite", "postgresql"] = Field(default="sqlite", description="Database type")
    DB_HOST: Optional[str] = Field(default=None, description="Database host")
    DB_PORT: Optional[int] = Field(default=None, description="Database port")
    DB_NAME: Optional[str] = Field(default=None, description="Database name")
    DB_USER: Optional[str] = Field(default=None, description="Database user")
    DB_PASSWORD: Optional[str] = Field(default=None, description="Database password")

    # Gradio UI settings
    GRADIO_SERVER_NAME: str = Field(default="127.0.0.1", description="Gradio server host")
    GRADIO_SERVER_PORT: int = Field(default=7860, ge=1024, le=65535, description="Gradio server port")
    GRADIO_SHARE: bool = Field(default=False, description="Create public Gradio share link")

    @validator("ENVIRONMENT", pre=True)
    def validate_environment(cls, v):
        """Validate environment value."""
        if isinstance(v, str):
            v = v.lower()
        valid = ["development", "staging", "production"]
        if v not in valid:
            raise ValueError(f"ENVIRONMENT must be one of {valid}")
        return v

    @validator("LOG_LEVEL", pre=True)
    def validate_log_level(cls, v):
        """Validate log level."""
        valid = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if isinstance(v, str) and v.upper() in valid:
            return v.upper()
        return "INFO"

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"

    @property
    def allowed_extensions_list(self) -> list[str]:
        """Get list of allowed file extensions."""
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    @property
    def allowed_hosts_list(self) -> list[str]:
        """Get list of allowed hosts."""
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",")]

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instantiate the settings
settings = Settings(
    ENVIRONMENT=ENVIRONMENT,
    GROQ_API_KEY=os.getenv("GROQ_API_KEY"),
    SECRET_KEY=os.getenv("SECRET_KEY", os.urandom(32).hex()),
)

# Create necessary directories if they don't exist
for dir_path in [
    settings.DATA_DIR,
    settings.LOGS_DIR,
    settings.EXPORTS_DIR,
    settings.CACHE_DIR,
    Path(settings.VECTOR_STORE_PATH),
]:
    os.makedirs(dir_path, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format=settings.LOG_FORMAT,
    handlers=[
        logging.FileHandler(settings.LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)
logger.info(f"Configuration loaded for environment: {settings.ENVIRONMENT}")
