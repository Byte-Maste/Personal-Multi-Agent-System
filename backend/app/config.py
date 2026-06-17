from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/personal_finance_agent"
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    GROQ_API_KEY: str = ""
    VOYAGE_API_KEY: str = ""
    VOYAGE_EMBED_MODEL: str = "voyage-3"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    UPLOAD_MAX_SIZE_MB: int = 50

    class Config:
        env_file = ".env"

settings = Settings()
