from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "AgriPlace User Service"
    database_url: str
    auth_service_url: str = "http://auth-service:8000"
    
    # We need JWT secrets to verify tokens sent by API Gateway / Frontend
    jwt_secret_key: str = "supersecretkey_change_in_production"
    jwt_algorithm: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()
