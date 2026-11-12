from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch):
    activities = {
        "Chess Club": {
            "description": "Play chess",
            "schedule": "Fridays",
            "max_participants": 12,
            "participants": ["existing@mergington.edu"],
        }
    }
    monkeypatch.setattr(app_module, "activities", activities)
    return TestClient(app_module.app)


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_data_without_caching(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert expected_activity in response.json()
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant_and_updates_activity_list(client):
    # Arrange
    activity = "Chess Club"
    email = "student@mergington.edu"

    # Act
    signup_response = client.post(
        f"/activities/{quote(activity, safe='')}/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert signup_response.status_code == 200
    assert signup_response.json() == {
        "message": f"Signed up {email} for {activity}"
    }
    assert activities_response.json()[activity]["participants"] == [
        "existing@mergington.edu",
        email,
    ]


def test_signup_rejects_duplicate_registration(client):
    # Arrange
    activity = "Chess Club"
    email = "existing@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{quote(activity, safe='')}/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Student is already signed up for this activity"
    )
    assert activities_response.json()[activity]["participants"] == [email]


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{quote(activity, safe='')}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_registered_student(client):
    # Arrange
    activity = "Chess Club"
    email = "existing@mergington.edu"

    # Act
    unregister_response = client.delete(
        f"/activities/{quote(activity, safe='')}/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert unregister_response.status_code == 200
    assert unregister_response.json() == {
        "message": f"Unregistered {email} from {activity}"
    }
    assert activities_response.json()[activity]["participants"] == []


def test_unregister_rejects_student_not_signed_up(client):
    # Arrange
    activity = "Chess Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{quote(activity, safe='')}/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Student is not signed up for this activity"
    )
    assert activities_response.json()[activity]["participants"] == [
        "existing@mergington.edu"
    ]


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity = "Unknown Club"

    # Act
    response = client.delete(
        f"/activities/{quote(activity, safe='')}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
