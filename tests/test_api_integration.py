import pytest
from fastapi import status

from app.core.config import settings


def test_create_and_get_session_flow(client, user_session_data):
    """Test the create session and get session flow."""
    # Step 1: Create a session
    response = client.post(
        f"{settings.API_V1_STR}/sessions/",
        json=user_session_data
    )
    assert response.status_code == status.HTTP_201_CREATED
    session_data = response.json()
    session_id = session_data["id"]
    
    # Step 2: Get the session
    response = client.get(f"{settings.API_V1_STR}/sessions/{session_id}")
    assert response.status_code == status.HTTP_200_OK
    retrieved_session = response.json()
    assert retrieved_session["id"] == session_id
    
    # Step 3: Update the session
    update_data = {"language": "fr-FR", "country": "FR"}
    response = client.patch(
        f"{settings.API_V1_STR}/sessions/{session_id}",
        json=update_data
    )
    assert response.status_code == status.HTTP_200_OK
    updated_session = response.json()
    assert updated_session["language"] == "fr-FR"
    assert updated_session["country"] == "FR"


def test_session_to_profile_flow(client, user_session_data, user_profile_data):
    """Test the flow from creating a session to creating a profile."""
    # Step 1: Create a session
    response = client.post(
        f"{settings.API_V1_STR}/sessions/",
        json=user_session_data
    )
    assert response.status_code == status.HTTP_201_CREATED
    session_data = response.json()
    session_id = session_data["id"]
    
    # Update the session ID in the profile data
    user_profile_data["session_id"] = session_id
    
    # Step 2: Create a profile linked to the session
    response = client.post(
        f"{settings.API_V1_STR}/profiles/",
        json=user_profile_data
    )
    assert response.status_code == status.HTTP_201_CREATED
    profile_data = response.json()
    profile_id = profile_data["id"]
    
    # Step 3: Get the session again to check if it's linked to the profile
    response = client.get(f"{settings.API_V1_STR}/sessions/{session_id}")
    assert response.status_code == status.HTTP_200_OK
    updated_session = response.json()
    assert "profile_id" in updated_session
    assert updated_session["profile_id"] == profile_id
    
    # Step 4: Get the profile
    response = client.get(f"{settings.API_V1_STR}/profiles/{profile_id}")
    assert response.status_code == status.HTTP_200_OK
    profile = response.json()
    assert profile["id"] == profile_id


def test_task_completion_flow(client, user_session_data):
    """Test the flow of recording task completions."""
    # Step 1: Create a session
    response = client.post(
        f"{settings.API_V1_STR}/sessions/",
        json=user_session_data
    )
    assert response.status_code == status.HTTP_201_CREATED
    session_data = response.json()
    session_id = session_data["id"]
    
    # Step 2: Record a task completion
    task_data = {
        "task_id": "task_123",
        "task_type": "vqa",
        "time_spent_ms": 5000,
        "successful": True
    }
    response = client.post(
        f"{settings.API_V1_STR}/sessions/{session_id}/task-completed",
        json=task_data
    )
    assert response.status_code == status.HTTP_200_OK
    updated_session = response.json()
    assert updated_session["tasks_completed"] == 1
    
    # Step 3: Record another task completion
    task_data = {
        "task_id": "task_124",
        "task_type": "text_classification",
        "time_spent_ms": 3000,
        "successful": True
    }
    response = client.post(
        f"{settings.API_V1_STR}/sessions/{session_id}/task-completed",
        json=task_data
    )
    assert response.status_code == status.HTTP_200_OK
    updated_session = response.json()
    assert updated_session["tasks_completed"] == 2
    
    # Step 4: Get the statistics for the session
    response = client.get(f"{settings.API_V1_STR}/statistics/sessions/{session_id}")
    assert response.status_code == status.HTTP_200_OK
    stats = response.json()
    assert stats["total_tasks_completed"] == 2
    assert stats["success_rate"] == 1.0  # Both tasks were successful


def test_expertise_areas_flow(client):
    """Test the flow of working with expertise areas."""
    # Step 1: Create an expertise area
    area_data = {
        "name": "Machine Learning",
        "slug": "machine-learning",
        "description": "Machine learning expertise area",
        "is_active": True
    }
    response = client.post(
        f"{settings.API_V1_STR}/expertise-areas/",
        json=area_data
    )
    assert response.status_code == status.HTTP_201_CREATED
    area = response.json()
    area_id = area["id"]
    
    # Step 2: Get the expertise area
    response = client.get(f"{settings.API_V1_STR}/expertise-areas/{area_id}")
    assert response.status_code == status.HTTP_200_OK
    retrieved_area = response.json()
    assert retrieved_area["id"] == area_id
    assert retrieved_area["name"] == area_data["name"]
    
    # Step 3: Create a child expertise area
    child_area_data = {
        "name": "Deep Learning",
        "slug": "deep-learning",
        "description": "Deep learning, a subset of machine learning",
        "parent_id": area_id,
        "is_active": True
    }
    response = client.post(
        f"{settings.API_V1_STR}/expertise-areas/",
        json=child_area_data
    )
    assert response.status_code == status.HTTP_201_CREATED
    child_area = response.json()
    child_area_id = child_area["id"]
    
    # Step 4: Get expertise area tree
    response = client.get(f"{settings.API_V1_STR}/expertise-areas/tree")
    assert response.status_code == status.HTTP_200_OK
    tree = response.json()
    assert "areas" in tree
    assert len(tree["areas"]) > 0
    
    # Find our root area in the tree
    root_area = next((a for a in tree["areas"] if a["id"] == area_id), None)
    assert root_area is not None
    assert "children" in root_area
    assert len(root_area["children"]) > 0
    assert root_area["children"][0]["id"] == child_area_id
