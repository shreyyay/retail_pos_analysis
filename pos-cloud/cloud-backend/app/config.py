from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://posuser:changeme@postgres:5432/posdb"
    CLAUDE_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-haiku-4-5-20251001"
    APP_ENV: str = "production"

    class Config:
        env_file = ".env"


settings = Settings()
