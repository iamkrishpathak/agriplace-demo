from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "AgriPlace Logistics Service"
    database_url: str
    user_service_url: str = "http://user-service:8000"
    ml_service_url: str = "http://ml-service:8000"
    jwt_secret_key: str = "supersecretkey_change_in_production"
    jwt_algorithm: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()
