import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Handle Render's legacy 'postgres://' connection string format if present
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    # Fallback to local SQLite for development if no database URL is set, 
    # but raise a warning or let it fail gracefully.
    DATABASE_URL = "sqlite:///local_fallback.db"

# Create SQLAlchemy engine
# Neon PostgreSQL requires SSL, which is usually appended to the connection string as ?sslmode=require
# If it's SQLite, we don't need pool_pre_ping or special arguments
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

# Create Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()

def get_db():
    """Dependency helper to get database session with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
