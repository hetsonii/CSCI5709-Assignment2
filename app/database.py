"""
Database connection and session management for the LEDGR API.

Reads DATABASE_URL from the environment. On Render, this is injected
automatically when a PostgreSQL instance is linked to the web service.
Locally, set it in a .env file (see .env.example).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ledgr_dev.db")

# Render's managed Postgres URLs start with "postgres://" but SQLAlchemy 1.4+
# requires "postgresql://". Normalize it here so the same code works both
# locally (sqlite fallback) and on Render (Postgres).
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session and guarantees closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
