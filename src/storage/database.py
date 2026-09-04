import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config import settings

DB_PATH = settings.DATABASE_URL

# Asegurar directorio data/
os.makedirs("data", exist_ok=True)

engine = create_engine(
    DB_PATH, 
    connect_args={"check_same_thread": False} if "sqlite" in DB_PATH else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
