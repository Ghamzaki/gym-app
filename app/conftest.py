# app/conftest.py
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.database import Base, get_db
from app.main import app

# 1. Configuration (No separate file needed for simplicity)
TEST_DATABASE_URL = "sqlite:///./test.db" 

# --- Fixtures ---

@pytest.fixture(scope="session")
def db_engine():
    """Sets up the database engine for the entire session."""
    engine = create_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    # Create tables before the session starts
    Base.metadata.create_all(bind=engine)
    yield engine
    # Cleanup: Drop tables and delete the file after the session ends
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture(scope="session")
def db_session(db_engine):
    """Creates a single database session for the dependency override."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    db_session = TestingSessionLocal()
    yield db_session
    db_session.close()

@pytest.fixture(scope="session")
def client(db_session):
    """Overrides the get_db dependency and provides a TestClient."""
    
    # 1. Dependency Override Function
    def override_get_db():
        """Yields the session-scoped test session."""
        try:
            yield db_session
        finally:
            # We don't close here as the session is closed in the db_session fixture yield
            pass

    # 2. Apply the Override
    app.dependency_overrides[get_db] = override_get_db
    
    # 3. Create the Test Client
    # TestClient internally uses httpx.Client and is fully compatible with FastAPI
    # This structure is highly stable and avoids scope/async issues.
    with TestClient(app) as test_client:
        yield test_client
    
    # 4. Clean up the Override (Good practice)
    app.dependency_overrides.clear()