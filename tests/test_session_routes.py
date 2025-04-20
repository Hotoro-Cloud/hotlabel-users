import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.models.user_session import UserSession
from app.core.config import settings


def test_create_session(client, user_session_data):
    """Test creating a new user session."""
    response = client.post(
        f"{settings.API_V1_STR}/sessions/",
        json=user_session_data
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["publisher_id"] == user_session_data["publisher_id"]
    assert data["browser_fingerprint"] == user_session_data["browser_fingerprint"]
    assert data["language"] == user_session_data["language"]
    assert "created_at" in data
    assert "updated_at" in data


def test_get_session(client, db, user_session_data):
    """Test retrieving a user session by ID."""
    # Create a session in the database
    session = UserSession(**user_session_data)
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Retrieve the session via API
    response = client.get(f"{settings.API_V1_STR}/sessions/{session.id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == session.id
    assert data["publisher_id"] == user_session_data["publisher_id"]
    assert data["browser_fingerprint"] == user_session_data["browser_fingerprint"]


def test_update_session(client, db, user_session_data):
    """Test updating a user session."""
    # Create a session in the database
    session = UserSession(**user_session_data)
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Update data
    update_data = {"language": "fr-FR", "country": "FR"}
    
    # Update via API
    response = client.patch(
        f"{settings.API_V1_STR}/sessions/{session.id}",
        json=update_data
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == session.id
    assert data["language"] == update_data["language"]
    assert data["country"] == update_data["country"]
    # Original data should be preserved
    assert data["publisher_id"] == user_session_data["publisher_id"]


def test_get_nonexistent_session(client):
    """Test retrieving a non-existent session."""
    response = client.get(f"{settings.API_V1_STR}/sessions/sess_nonexistent")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_record_task_completion(client, db, user_session_data):
    """Test recording a task completion for a session."""
    # Create a session in the database
    session = UserSession(**user_session_data)
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Task completion data
    task_data = {
        "task_id": "task_123",
        "task_type": "vqa",
        "time_spent_ms": 5000,
        "successful": True
    }
    
    # Record task completion
    response = client.post(
        f"{settings.API_V1_STR}/sessions/{session.id}/tasks",
        json=task_data
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "tasks_completed" in data
    assert data["tasks_completed"] == 1
    
    # Check that session was updated in the database
    db.refresh(session)
    assert session.tasks_completed == 1


def test_extend_session(client, db, user_session_data):
    """Test extending a session's expiration time."""
    # Create a session in the database
    session = UserSession(**user_session_data)
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Extend session
    response = client.post(f"{settings.API_V1_STR}/sessions/{session.id}/extend")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "last_active" in data
    assert "expires_at" in data
