from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "AgriPlace Payment Service"
    database_url: str
    jwt_secret_key: str = "supersecretkey_change_in_production"
    jwt_algorithm: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()
