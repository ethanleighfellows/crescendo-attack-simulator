from __future__ import annotations

from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """Application-level settings loaded from environment variables."""

    app_name: str = "Crescendo Jailbreak Generator"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    together_api_key: Optional[str] = None

    default_simulator_model: str = "gpt-4o-mini"
    default_target_model: str = "gpt-4o"
    default_temperature: float = 0.7
    max_retries: int = 3

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
