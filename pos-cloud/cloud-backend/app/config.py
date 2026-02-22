from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://posuser:changeme@postgres:5432/posdb"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-70b-versatile"
    APP_ENV: str = "production"

    class Config:
        env_file = ".env"


settings = Settings()
