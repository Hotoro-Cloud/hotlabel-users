import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
import app.api.routes.profiles
import app.api.routes.expertise
from app.main import app
from app.db.session import get_db
from app.core.config import settings

# Test database URL
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create the test engine
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    # Create the tables in the test database
    Base.metadata.create_all(bind=engine)
    
    # Create a test session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    
    # Drop the tables after the test is complete
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with a test database dependency."""
    # Override the get_db dependency to use our test database
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    # Use the test dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Create and return the test client
    with TestClient(app) as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def user_session_data():
    """Return example user session data for tests."""
    return {
        "publisher_id": "pub_test123",
        "browser_fingerprint": "f1ngerpr1nt123",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/90.0.4430.212",
        "language": "en-US",
        "timezone": "America/New_York",
        "referrer": "https://example.com",
        "country": "US",
        "device_type": "desktop",
        "platform": "Windows",
        "consent_given": True,
        "analytics_opt_in": True,
        "personalization_opt_in": True,
        "metadata": {"key": "value"}
    }


@pytest.fixture(scope="function")
def user_profile_data():
    """Return example user profile data for tests."""
    return {
        "email": "test@example.com",
        "session_id": "sess_test123",
        "display_name": "TestUser",
        "primary_language": "en-US",
        "additional_languages": ["fr", "es"],
        "timezone": "America/New_York",
        "notification_preferences": {"email": True, "push": False},
        "privacy_settings": {"share_expertise": True, "public_profile": False},
        "profile_metadata": {"interests": ["technology", "science"]}
    }


@pytest.fixture(scope="function")
def expertise_area_data():
    """Return example expertise area data for tests."""
    return {
        "name": "Machine Learning",
        "slug": "machine-learning",
        "description": "Machine learning expertise area",
        "is_active": True
    }
