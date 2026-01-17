import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """
    Application-wide settings and configuration.
    """

    # Base paths
    BASE_DIR: Path = Path(__file__).parent.parent.absolute()
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = BASE_DIR / "logs"

    # File paths
    LOG_FILE: str = str(LOGS_DIR / "qa_log.txt")

    # Vector DB paths for policy embeddings
    VECTOR_STORE_PATH: str = str(BASE_DIR / "vector_store")

    # Text splitting settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100

    # Model settings
    LLM_MODEL: str = "gemma2-9b-it"
    TEMPERATURE: float = 0.3
    MAX_TOKENS: int = 2048

    # Retrieval settings
    TOP_K_MATCHES: int = 3
    SIMILARITY_THRESHOLD: float = -1.0

    # Logging
    LOG_LEVEL: str = "INFO"
    ENABLE_DEBUG: bool = True

    # API keys
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")

    class Config:
        case_sensitive = True


# Instantiate the settings
settings = Settings()

# Create necessary directories if they don't exist
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.LOGS_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
