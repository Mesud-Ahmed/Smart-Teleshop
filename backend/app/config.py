from functools import lru_cache
import json

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "Zembil Vision API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    app_env: str = "development"

    supabase_url: str = ""
    supabase_key: str = ""
    supabase_products_table: str = "products"
    supabase_sales_table: str = "sales"
    supabase_storage_bucket: str = "product-images"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    embedding_model: str = "gemini-embedding-001"

    telegram_bot_token: str = ""
    backend_public_url: str = "http://localhost:8000"
    cors_origins_raw: str = "http://localhost:3000"
    frontend_app_url: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        raw = self.cors_origins_raw.strip()
        if not raw:
            return ["http://localhost:3000"]
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = []
            if isinstance(parsed, list):
                return [str(origin).strip() for origin in parsed if str(origin).strip()]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    @field_validator("cors_origins_raw", mode="before")
    @classmethod
    def normalize_cors_origins_raw(cls, value: str | list[str]) -> str:
        if isinstance(value, list):
            return ",".join(str(origin).strip() for origin in value if str(origin).strip())
        return value or "http://localhost:3000"

    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    def validate_runtime_requirements(self) -> None:
        if not self.is_production():
            return

        required = {
            "SUPABASE_URL": self.supabase_url,
            "SUPABASE_KEY": self.supabase_key,
            "GEMINI_API_KEY": self.gemini_api_key,
            "BACKEND_PUBLIC_URL": self.backend_public_url,
            "FRONTEND_APP_URL": self.frontend_app_url,
            "CORS_ORIGINS": self.cors_origins_raw,
            "SUPABASE_STORAGE_BUCKET": self.supabase_storage_bucket,
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            missing_csv = ", ".join(missing)
            raise ValueError(f"Missing required production environment variables: {missing_csv}")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_runtime_requirements()
    return settings
