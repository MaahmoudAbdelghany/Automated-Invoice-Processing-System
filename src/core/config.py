"""
Application Configuration Module.

Loads settings from environment variables (via .env file) using Pydantic Settings.
All other modules import their config from here.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root directory (two levels up from src/core/config.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Central application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    APP_NAME: str = "Automated Invoice Processing System"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # --- Server ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./invoices.db"

    # --- OCR ---
    TESSERACT_CMD: str = "tesseract"  # Path to Tesseract executable

    # --- File Upload ---
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".png", ".jpg", ".jpeg", ".tiff"]


# Singleton instance — import this throughout the app
settings = Settings()
