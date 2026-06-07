"""
Integration tests for the Activities API

Tests cover all endpoints:
- GET /activities
- POST /activities/{activity_name}/signup
- DELETE /activities/{activity_name}/remove
"""

import pytest
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Art Club": {
            "description": "Explore various art techniques and create your own masterpieces",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
            "participants": ["ava@mergington.edu", "liam@mergington.edu"]
        }
    })
    yield
    # Cleanup after test (optional, as we reset at the start)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities with correct structure"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all activities are returned
        assert len(data) == 4
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert "Art Club" in data

    def test_get_activities_structure(self, client):
        """Test that each activity has the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_activities_participants_populated(self, client):
        """Test that activities have participants populated"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds participant to activity"""
        # Initial check
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Signup
        client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
        
        # Verify participant was added
        response = client.get("/activities")
        new_count = len(response.json()["Chess Club"]["participants"])
        assert new_count == initial_count + 1
        assert "newstudent@mergington.edu" in response.json()["Chess Club"]["participants"]

    def test_signup_nonexistent_activity(self, client):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_already_signed_up(self, client):
        """Test signup fails if student already signed up for activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_multiple_activities(self, client):
        """Test that a student can sign up for multiple activities"""
        student_email = "multistudent@mergington.edu"
        
        # Sign up for Chess Club
        response1 = client.post(
            f"/activities/Chess Club/signup?email={student_email}"
        )
        assert response1.status_code == 200
        
        # Sign up for Art Club
        response2 = client.post(
            f"/activities/Art Club/signup?email={student_email}"
        )
        assert response2.status_code == 200
        
        # Verify both signups
        response = client.get("/activities")
        data = response.json()
        assert student_email in data["Chess Club"]["participants"]
        assert student_email in data["Art Club"]["participants"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/remove endpoint"""

    def test_remove_participant_success(self, client):
        """Test successful removal of a participant"""
        response = client.delete(
            "/activities/Chess Club/remove?email=michael@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_remove_participant_actually_removes(self, client):
        """Test that participant is actually removed from activity"""
        # Initial check
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        assert "michael@mergington.edu" in response.json()["Chess Club"]["participants"]
        
        # Remove participant
        client.delete("/activities/Chess Club/remove?email=michael@mergington.edu")
        
        # Verify participant was removed
        response = client.get("/activities")
        new_count = len(response.json()["Chess Club"]["participants"])
        assert new_count == initial_count - 1
        assert "michael@mergington.edu" not in response.json()["Chess Club"]["participants"]

    def test_remove_from_nonexistent_activity(self, client):
        """Test remove from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/remove?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_remove_nonexistent_participant(self, client):
        """Test remove of non-participant returns 400"""
        response = client.delete(
            "/activities/Chess Club/remove?email=nonexistent@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Participant not found" in data["detail"]

    def test_remove_all_participants(self, client):
        """Test removing all participants from an activity"""
        activity_name = "Chess Club"
        
        # Get all participants
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"].copy()
        
        # Remove each participant
        for email in participants:
            response = client.delete(
                f"/activities/{activity_name}/remove?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all removed
        response = client.get("/activities")
        assert len(response.json()[activity_name]["participants"]) == 0


class TestIntegrationWorkflow:
    """Integration tests for complete workflows"""

    def test_signup_then_remove_workflow(self, client):
        """Test complete workflow: signup then remove"""
        student_email = "workflow@mergington.edu"
        activity_name = "Chess Club"
        
        # Initial check - not signed up
        response = client.get("/activities")
        assert student_email not in response.json()[activity_name]["participants"]
        
        # Sign up
        response = client.post(
            f"/activities/{activity_name}/signup?email={student_email}"
        )
        assert response.status_code == 200
        
        # Verify signed up
        response = client.get("/activities")
        assert student_email in response.json()[activity_name]["participants"]
        
        # Remove
        response = client.delete(
            f"/activities/{activity_name}/remove?email={student_email}"
        )
        assert response.status_code == 200
        
        # Verify removed
        response = client.get("/activities")
        assert student_email not in response.json()[activity_name]["participants"]

    def test_multiple_operations_workflow(self, client):
        """Test complex workflow with multiple signups and removals"""
        students = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        # Sign up all students
        for email in students:
            response = client.post(
                f"/activities/Programming Class/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all signed up
        response = client.get("/activities")
        participants = response.json()["Programming Class"]["participants"]
        for email in students:
            assert email in participants
        
        # Remove middle student
        response = client.delete(
            f"/activities/Programming Class/remove?email={students[1]}"
        )
        assert response.status_code == 200
        
        # Try to remove again (should fail)
        response = client.delete(
            f"/activities/Programming Class/remove?email={students[1]}"
        )
        assert response.status_code == 400
        
        # Verify state
        response = client.get("/activities")
        participants = response.json()["Programming Class"]["participants"]
        assert students[0] in participants
        assert students[1] not in participants
        assert students[2] in participants
