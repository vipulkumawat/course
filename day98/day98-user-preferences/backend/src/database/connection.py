from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..preferences.models.user import Base
from ..config.settings import settings

# Use SQLite for local development (simpler setup)
database_url = "sqlite:///./preferences.db"
engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)
