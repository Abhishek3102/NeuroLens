import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """
    Manages application settings loaded from a .env file.
    """
    # Load from .env file
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # MongoDB
    MONGO_CONNECTION_STRING: str = "mongodb://localhost:27017/"
    DATABASE_NAME: str = "resume_analyzer_db"

    # Google Gemini
    GEMINI_API_KEY: str

    # Logging
    LOG_LEVEL: str = "INFO"

@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached instance of the application settings.
    This ensures the .env file is read only once.
    """
    logging.info("Loading application settings...")
    try:
        settings = Settings()
        return settings
    except Exception as e:
        logging.error(f"Error loading settings: {e}")
        raise

# Instantiate settings once
settings = get_settings()
