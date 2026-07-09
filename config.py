"""Application configuration."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    business_id: str = "default-business"
    business_name: str = "Acme Home Services"
    business_type: str = "home services"
    owner_first_name: str = "Sam"

    host: str = "0.0.0.0"
    port: int = 8002
    public_base_url: str = "http://localhost:8002"
    log_level: str = "INFO"

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    owner_phone_number: str = ""
    validate_twilio_signature: bool = True
    sms_dry_run: bool = False

    mistral_api_key: str = ""
    primary_model: str = "mistral/mistral-small-latest"
    fallback_model: str = "mistral/ministral-3b-latest"
    llm_timeout_seconds: float = 6.0

    supabase_url: str = ""
    supabase_key: str = ""

    demo_mode_enabled: bool = True
    demo_owner_phone_number: str = "+15550002222"

    duplicate_window_hours: int = 4
    max_texts_per_window: int = 3
    max_exchanges: int = 8
    conversation_timeout_minutes: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
