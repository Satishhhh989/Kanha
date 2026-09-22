from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, ValidationError

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = ROOT_DIR / ".env"

class KahnaSettings(BaseSettings):
    """
    Central configuration object for KAHNA.
    
    Environment variables are automatically mapped to these fields.
    """
    
    # Environment
    environment: str = Field(default="development", alias="KAHNA_ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="KAHNA_LOG_LEVEL")
    
    # API / Server
    host: str = Field(default="127.0.0.1", alias="KAHNA_HOST")
    port: int = Field(default=8765, alias="KAHNA_PORT")
    
    # AI Provider (OpenRouter)
    openrouter_api_key: str = Field(alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="meta-llama/llama-3-8b-instruct", alias="OPENROUTER_MODEL")
    
    # Phase 4: Remote Intelligence
    telegram_bot_token: str | None = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_allowed_user_id: str | None = Field(default=None, alias="TELEGRAM_ALLOWED_USER_ID")
    kahna_device_id: str = Field(default="kahna-local-device", alias="KAHNA_DEVICE_ID")
    kahna_device_secret: str = Field(default="unsafe-default-secret", alias="KAHNA_DEVICE_SECRET")
    
    model_config = SettingsConfigDict(
        env_file=(str(ENV_PATH), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

def load_settings() -> KahnaSettings:
    """Loads and validates the configuration from environment variables or .env file."""
    try:
        return KahnaSettings()
    except ValidationError:
        import os
        import logging
        logging.getLogger("core.config").warning(
            "OPENROUTER_API_KEY not found in environment or .env. Using default placeholder."
        )
        return KahnaSettings(
            _env_file=None,
            OPENROUTER_API_KEY=os.environ.get("OPENROUTER_API_KEY", "your_openrouter_api_key_here")
        )

# Global settings instance, loaded eagerly
settings = load_settings()
