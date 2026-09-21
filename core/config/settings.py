from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

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
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

def load_settings() -> KahnaSettings:
    """Loads and validates the configuration from environment variables or .env file."""
    # This will raise validation errors if required fields (like OPENROUTER_API_KEY) are missing.
    return KahnaSettings()

# Global settings instance, loaded eagerly
settings = load_settings()
