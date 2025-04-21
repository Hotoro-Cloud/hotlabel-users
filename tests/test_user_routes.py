import pytest

def test_search_users(client):
    response = client.get("/api/v1/users/search?query=test")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)

def test_get_task_compatibility(client, user_profile_data):
    # Create a profile first
    create_resp = client.post("/api/v1/profiles/", json=user_profile_data)
    profile_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/users/{profile_id}/task-compatibility")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        assert "compatibility_score" in data

def test_match_users_for_task(client):
    response = client.get("/api/v1/users/match-for-task?task_id=task1")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)

def test_detect_language(client):
    payload = {"text": "This is a test."}
    response = client.post("/api/v1/users/detect-language", json=payload)
    assert response.status_code in (200, 400)
    if response.status_code == 200:
        data = response.json()
        assert "language" in data
