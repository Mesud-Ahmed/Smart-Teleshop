from functools import lru_cache

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
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    frontend_app_url: str = "http://localhost:3000"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        if not value:
            return ["http://localhost:3000"]
        return [origin.strip() for origin in value.split(",") if origin.strip()]

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
            "CORS_ORIGINS": ",".join(self.cors_origins),
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
