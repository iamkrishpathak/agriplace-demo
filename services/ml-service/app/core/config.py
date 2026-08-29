from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "AgriPlace ML Service"
    database_url: str
    jwt_secret_key: str = "supersecretkey_change_in_production"
    jwt_algorithm: str = "HS256"
    models_dir: str = "/app/models"

    class Config:
        env_file = ".env"

settings = Settings()
