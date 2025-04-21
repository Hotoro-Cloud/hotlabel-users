import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.services.profiler_service import ProfilerService
from app.db.repositories.user_session_repository import UserSessionRepository
from app.db.repositories.user_profile_repository import UserProfileRepository
from app.db.repositories.expertise_area_repository import ExpertiseAreaRepository
from app.models.user_session import UserSession
from app.models.user_profile import UserProfile
from app.models.expertise_area import ExpertiseArea


@pytest.fixture
def profiler_service(db):
    """Create a ProfilerService instance with mocked repositories."""
    session_repo = UserSessionRepository()
    profile_repo = UserProfileRepository()
    statistics_repo = None  # Add a placeholder or mock if needed
    expertise_repo = ExpertiseAreaRepository()
    return ProfilerService(session_repo, profile_repo, statistics_repo, expertise_repo)


def test_analyze_browser_signals(profiler_service, user_session_data):
    """Test analyzing browser signals for user profiling."""
    # Setup
    browser_signals = {
        "language": "en-US",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/90.0.4430.212",
        "timezone": "America/New_York",
        "referrer": "https://example.com/technology",
        "screen_resolution": "1920x1080",
        "color_depth": 24,
    }
    
    # Call the method
    result = profiler_service.analyze_browser_signals(browser_signals)
    
    # Assertions
    assert result is not None
    assert "language" in result
    assert result["language"] == "en-US"
    assert "device_type" in result
    assert result["device_type"] == "desktop"
    assert "browser" in result
    assert "Chrome" in result["browser"]
    assert "operating_system" in result
    assert "Windows" in result["operating_system"]


def test_infer_expertise_areas(profiler_service, db):
    """Test inferring expertise areas from browsing patterns."""
    # Create expertise areas
    technology = ExpertiseArea(name="Technology", slug="technology", description="Technology domain")
    gaming = ExpertiseArea(name="Gaming", slug="gaming", description="Gaming domain")
    science = ExpertiseArea(name="Science", slug="science", description="Science domain")
    
    db.add_all([technology, gaming, science])
    db.commit()
    
    # Setup browsing data
    browsing_patterns = {
        "visited_pages": [
            "https://example.com/technology/ai",
            "https://example.com/technology/programming",
            "https://example.com/science/physics"
        ],
        "time_spent": {
            "technology": 120,
            "science": 45,
            "gaming": 5
        },
        "search_queries": ["machine learning", "python programming", "quantum physics"]
    }
    
    # Call the method
    result = profiler_service.infer_expertise_areas(browsing_patterns)
    
    # Assertions
    assert result is not None
    assert len(result) >= 2
    assert any(area["slug"] == "technology" for area in result)
    assert any(area["slug"] == "science" for area in result)
    
    # Check scores
    technology_area = next(area for area in result if area["slug"] == "technology")
    science_area = next(area for area in result if area["slug"] == "science")
    
    assert technology_area["confidence"] > science_area["confidence"]


def test_determine_language_proficiency(profiler_service):
    """Test determining language proficiency."""
    # Setup language signals
    language_signals = {
        "browser_language": "en-US",
        "content_languages": ["en", "fr", "es"],
        "interaction_time": {
            "en": 120,
            "fr": 45,
            "es": 5
        },
        "form_inputs": {
            "en": 50,
            "fr": 10,
            "es": 0
        }
    }
    
    # Call the method
    result = profiler_service.determine_language_proficiency(language_signals)
    
    # Assertions
    assert result is not None
    assert "primary" in result
    assert result["primary"] == "en"
    assert "proficiency" in result
    assert "en" in result["proficiency"]
    assert result["proficiency"]["en"] > result["proficiency"]["fr"]
    assert result["proficiency"]["fr"] > result["proficiency"]["es"]


def test_calculate_expertise_level(profiler_service, db, user_session_data):
    """Test calculating expertise level based on task history."""
    # Create a session
    session = UserSession(**user_session_data)
    session.tasks_completed = 55  # This should be level 2
    db.add(session)
    db.commit()
    
    # Call the method
    result = profiler_service.calculate_expertise_level(session.id)
    
    # Assertions
    assert result is not None
    assert "level" in result
    assert result["level"] == 2  # Based on default thresholds [10, 50, 100, 250]
    assert "next_level_threshold" in result
    assert result["next_level_threshold"] == 100
    assert "progress_percentage" in result
    # 55 completed tasks, 5 progress into the 50-100 range (50 tasks)
    assert result["progress_percentage"] == 10  # (55-50)/50 * 100 = 10%
