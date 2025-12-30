import pytest
from fastapi.testclient import TestClient


def test_root_redirect(client: TestClient):
    """Test that root endpoint redirects to static/index.html"""
    response = client.get("/")
    assert response.status_code == 200
    # FastAPI's RedirectResponse returns the content of the redirected page
    assert "text/html" in response.headers.get("content-type", "")


def test_get_activities(client: TestClient):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()

    # Check that we have activities
    assert isinstance(data, dict)
    assert len(data) > 0

    # Check structure of first activity
    first_activity = next(iter(data.values()))
    assert "description" in first_activity
    assert "schedule" in first_activity
    assert "max_participants" in first_activity
    assert "participants" in first_activity
    assert isinstance(first_activity["participants"], list)


def test_signup_successful(client: TestClient):
    """Test successful signup for an activity"""
    # Get initial activities to find one to test with
    response = client.get("/activities")
    activities = response.json()
    activity_name = list(activities.keys())[0]
    initial_participants = activities[activity_name]["participants"].copy()

    # Test signup
    email = "test@example.com"
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity_name in data["message"]

    # Verify participant was added
    response = client.get("/activities")
    activities = response.json()
    assert email in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == len(initial_participants) + 1


def test_signup_duplicate(client: TestClient):
    """Test signing up for the same activity twice"""
    # Get an activity and sign up once
    response = client.get("/activities")
    activities = response.json()
    activity_name = list(activities.keys())[0]
    email = "duplicate@example.com"

    # First signup should succeed
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert response.status_code == 200

    # Second signup should fail
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already signed up" in data["detail"]


def test_signup_nonexistent_activity(client: TestClient):
    """Test signing up for a non-existent activity"""
    response = client.post("/activities/NonExistentActivity/signup", params={"email": "test@example.com"})
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]


def test_unregister_successful(client: TestClient):
    """Test successful unregister from an activity"""
    # First sign up
    response = client.get("/activities")
    activities = response.json()
    activity_name = list(activities.keys())[0]
    email = "unregister@example.com"

    client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Get count before unregister
    response = client.get("/activities")
    activities = response.json()
    initial_count = len(activities[activity_name]["participants"])

    # Unregister
    response = client.post(f"/activities/{activity_name}/unregister", params={"email": email})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity_name in data["message"]

    # Verify participant was removed
    response = client.get("/activities")
    activities = response.json()
    assert email not in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == initial_count - 1


def test_unregister_not_signed_up(client: TestClient):
    """Test unregistering when not signed up"""
    response = client.get("/activities")
    activities = response.json()
    activity_name = list(activities.keys())[0]
    email = "notsignedup@example.com"

    response = client.post(f"/activities/{activity_name}/unregister", params={"email": email})
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "not signed up" in data["detail"]


def test_unregister_nonexistent_activity(client: TestClient):
    """Test unregistering from a non-existent activity"""
    response = client.post("/activities/NonExistentActivity/unregister", params={"email": "test@example.com"})
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]