import os

import pytest
import requests

HOST = os.environ.get("HOST", "http://localhost:8000")


@pytest.mark.api
class TestActivityAPI:
    """Test cases for activity API endpoints."""

    def test_get_activities_endpoint(self):
        """Test GET /api/activities/ endpoint."""
        response = requests.get(f"{HOST}/api/activities/")
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, list)

    def test_get_activity_by_id_not_found(self):
        """Test GET /api/activities/{id} with nonexistent ID."""
        response = requests.get(f"{HOST}/api/activities/999999")
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_activities_response_structure(self):
        """Test the structure of activities response."""
        response = requests.get(f"{HOST}/api/activities/")
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, list)
