from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://tasktracker:tasktracker@localhost:5432/tasktracker"
    storage_path: str = "./storage/uploads"
    max_upload_size_mb: int = 10
    telegram_allowed_user_ids: Annotated[list[int], NoDecode] = []

    @field_validator("telegram_allowed_user_ids", mode="before")
    @classmethod
    def parse_allowed_user_ids(cls, value):
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, int):
            return [value]
        # Accept both comma-separated ("1,2") and JSON ("[1, 2]") forms.
        text = str(value).strip()
        if text.startswith("["):
            import json

            parsed = json.loads(text)
            return parsed if isinstance(parsed, list) else [parsed]
        return [int(part) for part in text.split(",") if part.strip()]


settings = Settings()
