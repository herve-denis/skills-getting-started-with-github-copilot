"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestActivities:
    """Test the /activities endpoint"""

    def test_get_activities(self):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities

    def test_activity_structure(self):
        """Test that each activity has the required structure"""
        response = client.get("/activities")
        activities = response.json()

        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Test the signup endpoint"""

    def test_signup_valid(self):
        """Test signing up a student for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=test@example.com"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@example.com" in data["message"]

    def test_signup_duplicate(self):
        """Test that a student cannot sign up twice for the same activity"""
        email = "duplicate@example.com"
        # First signup
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200

        # Second signup should fail
        response2 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response2.status_code == 400
        data = response2.json()
        assert "detail" in data

    def test_signup_activity_not_found(self):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@example.com"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_at_capacity(self):
        """Test signing up when activity is at capacity"""
        # This test checks that participants can be added if under capacity
        response = client.get("/activities")
        activities = response.json()

        for activity_name, activity_data in activities.items():
            if (len(activity_data["participants"]) <
                    activity_data["max_participants"]):
                # Should be able to sign up
                response = client.post(
                    f"/activities/{activity_name}/signup?email=capacity@example.com"
                )
                assert response.status_code == 200
                break


class TestUnregister:
    """Test the unregister endpoint"""

    def test_unregister_valid(self):
        """Test unregistering a student from an activity"""
        email = "unregister@example.com"
        # First sign up
        client.post(f"/activities/Drama Club/signup?email={email}")

        # Then unregister
        response = client.delete(
            f"/activities/Drama Club/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_not_signed_up(self):
        """Test unregistering a student who is not signed up"""
        response = client.delete(
            "/activities/Basketball Team/unregister?email=notsignedup@example.com"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_activity_not_found(self):
        """Test unregistering from a non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=test@example.com"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]


class TestRoot:
    """Test the root endpoint"""

    def test_root_redirect(self):
        """Test that root endpoint redirects to static files"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestIntegration:
    """Integration tests for the full workflow"""

    def test_signup_and_unregister_workflow(self):
        """Test the complete workflow of signing up and unregistering"""
        email = "workflow@example.com"
        activity = "Art Studio"

        # Verify activity exists
        response = client.get("/activities")
        assert response.status_code == 200

        # Sign up
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200

        # Verify participant is added
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity]["participants"]

        # Unregister
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200

        # Verify participant is removed
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities[activity]["participants"]
