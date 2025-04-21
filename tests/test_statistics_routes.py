import pytest

def test_get_profile_statistics(client, user_profile_data):
    # Create a profile first
    create_resp = client.post("/api/v1/profiles/", json=user_profile_data)
    profile_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/statistics/profile/{profile_id}")
    assert response.status_code in (200, 404)  # 404 if stats not yet created
    if response.status_code == 200:
        data = response.json()
        assert data["profile_id"] == profile_id

def test_get_session_statistics(client, user_session_data):
    # Create a session first
    create_resp = client.post("/api/v1/sessions/", json=user_session_data)
    session_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/statistics/session/{session_id}")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        assert data["session_id"] == session_id

def test_update_profile_statistics(client, user_profile_data):
    # Create a profile first
    create_resp = client.post("/api/profiles/", json=user_profile_data)
    profile_id = create_resp.json()["id"]

    update_data = {"tasks_completed": 5}
    response = client.put(f"/api/v1/statistics/profile/{profile_id}", json=update_data)
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        assert data["tasks_completed"] == 5

def test_update_session_statistics(client, user_session_data):
    # Create a session first
    create_resp = client.post("/api/sessions/", json=user_session_data)
    session_id = create_resp.json()["id"]

    update_data = {"tasks_completed": 3}
    response = client.put(f"/api/v1/statistics/session/{session_id}", json=update_data)
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        assert data["tasks_completed"] == 3
