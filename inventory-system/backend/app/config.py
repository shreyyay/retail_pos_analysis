from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LangExtract / Gemini
    LANGEXTRACT_API_KEY: str = ""

    # Google Cloud Vision
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    # ERPNext
    ERPNEXT_URL: str = ""
    ERPNEXT_API_KEY: str = ""
    ERPNEXT_API_SECRET: str = ""

    # App settings
    UPLOAD_DIR: str = "/tmp/invoice_uploads"
    DEFAULT_WAREHOUSE: str = "Stores - Company"
    DEFAULT_COMPANY: str = "My Company"
    SQLITE_DB_PATH: str = "/app/data/pos_local.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
