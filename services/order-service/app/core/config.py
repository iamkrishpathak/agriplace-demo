from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "AgriPlace Order Service"
    database_url: str
    user_service_url: str = "http://user-service:8000"
    marketplace_service_url: str = "http://marketplace-service:8000"
    payment_service_url: str = "http://payment-service:8000"
    logistics_service_url: str = "http://logistics-service:8000"
    jwt_secret_key: str = "supersecretkey_change_in_production"
    jwt_algorithm: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()
