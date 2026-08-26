from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AgriPlace"
    environment: str = "development"
    database_url: str = "sqlite:///./agriplace.db"
    jwt_secret_key: str = Field(
        default="change-me-for-production",
        description="Use a strong secret in production; never commit real secrets.",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    data_gov_api_key: str | None = None
    routing_provider: str = "derived-haversine-demo"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

