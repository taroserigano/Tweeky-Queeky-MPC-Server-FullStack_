from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PORT: int = 5000
    MONGO_URI: str = "mongodb://localhost:27017/tweekyqueeky"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 30
    PAYPAL_CLIENT_ID: str
    PAYPAL_APP_SECRET: str
    PAYPAL_API_URL: str = "https://api-m.sandbox.paypal.com"
    NODE_ENV: str = "development"
    PAGINATION_LIMIT: int = 12

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
