import pytest
from pydantic import ValidationError
from core.config.settings import KahnaSettings

def test_config_validation(monkeypatch):
    # Set env vars to avoid reading .env
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    monkeypatch.setenv("KAHNA_ENVIRONMENT", "test")
    monkeypatch.setenv("KAHNA_LOG_LEVEL", "DEBUG")
    
    config = KahnaSettings()
    assert config.openrouter_api_key == "test_key"
    assert config.environment == "test"
    assert config.log_level == "DEBUG"

def test_config_missing_required(monkeypatch):
    # Ensure OPENROUTER_API_KEY is not set
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValidationError):
        KahnaSettings(_env_file=None)
