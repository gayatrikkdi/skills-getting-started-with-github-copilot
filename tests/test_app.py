"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
import copy

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


# Store original activities data
ORIGINAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture
def client_with_fresh_app():
    """Create a fresh test client with reset activities state"""
    # Reset activities to original state
    activities.clear()
    activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))
    return TestClient(app)


client = TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client_with_fresh_app):
        """Test that root endpoint redirects to /static/index.html"""
        response = client_with_fresh_app.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "static/index.html" in response.headers["location"]


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client_with_fresh_app):
        """Test that all activities are returned"""
        response = client_with_fresh_app.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that all expected activities are present
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Basketball" in data
        assert "Tennis Club" in data
        assert "Drama Club" in data
        assert "Art Studio" in data
        assert "Math Club" in data
        assert "Science Club" in data
        assert "Gym Class" in data
    
    def test_activity_has_required_fields(self, client_with_fresh_app):
        """Test that each activity has required fields"""
        response = client_with_fresh_app.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_initial_participants_correct(self, client_with_fresh_app):
        """Test that initial participant lists are correct"""
        response = client_with_fresh_app.get("/activities")
        data = response.json()
        
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
        assert "emma@mergington.edu" in data["Programming Class"]["participants"]


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant(self, client_with_fresh_app):
        """Test signing up a new participant"""
        response = client_with_fresh_app.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "signed up successfully" in data["message"]
    
    def test_signup_verification(self, client_with_fresh_app):
        """Test that signup actually adds the participant"""
        email = "testuser@mergington.edu"
        
        # Sign up
        response = client_with_fresh_app.post(
            "/activities/Chess%20Club/signup?email=" + email
        )
        assert response.status_code == 200
        
        # Verify participant was added
        response = client_with_fresh_app.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]
    
    def test_signup_duplicate_participant(self, client_with_fresh_app):
        """Test that duplicate signup is rejected"""
        response = client_with_fresh_app.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity(self, client_with_fresh_app):
        """Test signup for non-existent activity"""
        response = client_with_fresh_app.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_increments_participant_count(self, client_with_fresh_app):
        """Test that signup increments participant count"""
        email = "counter@mergington.edu"
        
        # Get initial count
        response = client_with_fresh_app.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Sign up
        client_with_fresh_app.post(
            "/activities/Chess%20Club/signup?email=" + email
        )
        
        # Check new count
        response = client_with_fresh_app.get("/activities")
        new_count = len(response.json()["Chess Club"]["participants"])
        
        assert new_count == initial_count + 1


class TestUnregisterEndpoint:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant(self, client_with_fresh_app):
        """Test unregistering an existing participant"""
        response = client_with_fresh_app.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "unregistered successfully" in data["message"]
    
    def test_unregister_verification(self, client_with_fresh_app):
        """Test that unregister actually removes the participant"""
        email = "michael@mergington.edu"
        
        # Unregister
        response = client_with_fresh_app.delete(
            f"/activities/Chess%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        response = client_with_fresh_app.get("/activities")
        data = response.json()
        assert email not in data["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_participant(self, client_with_fresh_app):
        """Test unregistering a nonexistent participant"""
        response = client_with_fresh_app.delete(
            "/activities/Chess%20Club/unregister?email=nonexistent@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_nonexistent_activity(self, client_with_fresh_app):
        """Test unregistering from non-existent activity"""
        response = client_with_fresh_app.delete(
            "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_decrements_participant_count(self, client_with_fresh_app):
        """Test that unregister decrements participant count"""
        email = "michael@mergington.edu"
        
        # Get initial count
        response = client_with_fresh_app.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Unregister
        client_with_fresh_app.delete(
            f"/activities/Chess%20Club/unregister?email={email}"
        )
        
        # Check new count
        response = client_with_fresh_app.get("/activities")
        new_count = len(response.json()["Chess Club"]["participants"])
        
        assert new_count == initial_count - 1


class TestCompleteFlow:
    """Tests for complete signup/unregister flows"""
    
    def test_signup_then_unregister(self, client_with_fresh_app):
        """Test signing up and then unregistering"""
        email = "flowtest@mergington.edu"
        activity = "Basketball"
        
        # Sign up
        response = client_with_fresh_app.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify signup
        response = client_with_fresh_app.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client_with_fresh_app.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify unregister
        response = client_with_fresh_app.get("/activities")
        assert email not in response.json()[activity]["participants"]
    
    def test_multiple_signup_and_unregister(self, client_with_fresh_app):
        """Test multiple signups and unregisters"""
        test_emails = [
            "test1@mergington.edu",
            "test2@mergington.edu",
            "test3@mergington.edu"
        ]
        activity = "Tennis Club"
        
        # Sign up all
        for email in test_emails:
            response = client_with_fresh_app.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all signed up
        response = client_with_fresh_app.get("/activities")
        participants = response.json()[activity]["participants"]
        for email in test_emails:
            assert email in participants
        
        # Unregister middle one
        client_with_fresh_app.delete(
            f"/activities/{activity}/unregister?email={test_emails[1]}"
        )
        
        # Verify correct unregister
        response = client_with_fresh_app.get("/activities")
        participants = response.json()[activity]["participants"]
        assert test_emails[0] in participants
        assert test_emails[1] not in participants
        assert test_emails[2] in participants
