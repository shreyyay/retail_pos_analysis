from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_raw_connection():
    """Return a raw psycopg2 connection — used by the LLM service for plain SQL."""
    return engine.raw_connection()


def init_db():
    from app.models import tally, udhar, followup  # noqa: F401 — registers tables
    Base.metadata.create_all(bind=engine)
