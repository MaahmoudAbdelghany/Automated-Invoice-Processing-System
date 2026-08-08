"""
Application Configuration Module.

Loads settings from environment variables (via .env file) using Pydantic Settings.
All other modules import their config from here:

    from src.config import settings
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root directory (one level up from src/config.py)
BASE_DIR = Path(__file__).resolve().parent.parent


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
    LOG_LEVEL: str = "INFO"

    # --- AWS General ---
    AWS_REGION: str = "us-east-1"

    # --- AWS S3 ---
    S3_BUCKET_NAME: str = ""
    S3_UPLOAD_PREFIX: str = "uploads/"

    # --- AWS DynamoDB ---
    DYNAMODB_TABLE_NAME: str = "invoices"

    # --- AWS Textract (OCR) ---
    TEXTRACT_REGION: str = ""  # Falls back to AWS_REGION if empty

    # --- AWS Bedrock (NLP) ---
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    BEDROCK_REGION: str = ""  # Falls back to AWS_REGION if empty

    # --- AWS SES (Notifications) ---
    SES_SENDER_EMAIL: str = ""
    SES_REGION: str = ""  # Falls back to AWS_REGION if empty

    # --- Processing ---
    CONFIDENCE_THRESHOLD: float = 0.85  # Below this triggers HITL review
    DEFAULT_LANGUAGE: str = "ar"  # Arabic-first
    SUPPORTED_LANGUAGES: list[str] = ["ar", "en"]

    # --- File Upload ---
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".png", ".jpg", ".jpeg", ".tiff"]


# Singleton instance — import this throughout the app
settings = Settings()
