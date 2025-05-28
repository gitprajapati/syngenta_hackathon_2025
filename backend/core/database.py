#core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from .config import settings

if "sqlite" in settings.DATABASE_URL:
    db_path = Path(settings.DATABASE_URL.split("///")[-1])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.touch(exist_ok=True)

engine = create_engine(settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()