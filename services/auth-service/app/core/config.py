from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "AgriPlace Auth Service"
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    user_service_url: str = "http://user-service:8000"

    class Config:
        env_file = ".env"

settings = Settings()
