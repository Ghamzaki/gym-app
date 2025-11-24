# app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- Supabase/PostgreSQL Integration ---
# Prioritize DATABASE_URL environment variable for production/Supabase, 
# falling back to SQLite for easy local testing if the variable is missing.
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "sqlite:///./sql_app.db"  # Local fallback
)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args
)
# ---

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()