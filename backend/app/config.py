from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./data/pos.db"
    SECRET_KEY: str = "dev-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ENVIRONMENT: str = "development"
    ADMIN_USER: str = "sysadmin"
    ADMIN_PASSWORD: str = "admin123"

    class Config:
        env_file = ".env"

settings = Settings()