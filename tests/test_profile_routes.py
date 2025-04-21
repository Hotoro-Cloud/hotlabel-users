import pytest

def test_create_profile(client, user_profile_data):
    response = client.post("/api/v1/profiles/", json=user_profile_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["email"] == user_profile_data["email"]

def test_get_profile(client, user_profile_data):
    # Create profile first
    create_resp = client.post("/api/v1/profiles/", json=user_profile_data)
    profile_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/profiles/{profile_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == profile_id

def test_update_profile(client, user_profile_data):
    # Create profile first
    create_resp = client.post("/api/profiles/", json=user_profile_data)
    profile_id = create_resp.json()["id"]

    update_data = {"display_name": "Updated Name"}
    response = client.put(f"/api/v1/profiles/{profile_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Updated Name"

def test_delete_profile(client, user_profile_data):
    # Create profile first
    create_resp = client.post("/api/profiles/", json=user_profile_data)
    profile_id = create_resp.json()["id"]

    response = client.delete(f"/api/v1/profiles/{profile_id}")
    assert response.status_code == 204

    # Ensure profile is deleted
    get_resp = client.get(f"/api/v1/profiles/{profile_id}")
    assert get_resp.status_code == 404

def test_list_profiles(client, user_profile_data):
    # Create a profile
    client.post("/api/v1/profiles/", json=user_profile_data)
    response = client.get("/api/v1/profiles/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(profile["email"] == user_profile_data["email"] for profile in data)
