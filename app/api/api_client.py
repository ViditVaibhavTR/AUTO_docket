"""
API Client for frontend integration with FastAPI backend.
This module provides functions to interact with the REST API.
"""

import requests
from typing import List, Optional, Dict, Any


class DocketAlertAPIClient:
    """Client for interacting with Docket Alert Automation API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize API client.

        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url
        self.session = requests.Session()

    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def get_docket_categories(self) -> Dict[str, Any]:
        """Get available docket categories."""
        response = self.session.get(f"{self.base_url}/api/v1/docket-categories")
        response.raise_for_status()
        return response.json()

    def get_states(self) -> List[str]:
        """Get available states."""
        response = self.session.get(f"{self.base_url}/api/v1/states")
        response.raise_for_status()
        return response.json()["states"]

    def get_districts(self, state: str) -> List[str]:
        """Get available districts for a state."""
        response = self.session.get(
            f"{self.base_url}/api/v1/districts",
            params={"state": state}
        )
        response.raise_for_status()
        return response.json()["districts"]

    def start_automation(self, include_docket: bool = False) -> Dict[str, Any]:
        """
        Start the automation process.

        Args:
            include_docket: Whether to include docket selection

        Returns:
            Response with session_id and status
        """
        response = self.session.post(
            f"{self.base_url}/api/v1/automation/start",
            json={"include_docket": include_docket}
        )
        response.raise_for_status()
        return response.json()

    def select_docket(
        self,
        session_id: str,
        category: str,
        specific_docket: str
    ) -> Dict[str, Any]:
        """
        Select a docket category and specific docket.

        Args:
            session_id: Browser session ID
            category: Docket category (e.g., "Dockets by State")
            specific_docket: Specific docket name (e.g., "California")

        Returns:
            Response with status
        """
        response = self.session.post(
            f"{self.base_url}/api/v1/docket/select",
            json={
                "session_id": session_id,
                "category": category,
                "specific_docket": specific_docket
            }
        )
        response.raise_for_status()
        return response.json()

    def select_district(
        self,
        session_id: str,
        state: str,
        district: str
    ) -> Dict[str, Any]:
        """
        Select a district for the chosen state.

        Args:
            session_id: Browser session ID
            state: State name
            district: District name (e.g., "Central District")

        Returns:
            Response with status
        """
        response = self.session.post(
            f"{self.base_url}/api/v1/district/select",
            json={
                "session_id": session_id,
                "state": state,
                "district": district
            }
        )
        response.raise_for_status()
        return response.json()

    def search_docket(
        self,
        session_id: str,
        docket_number: str
    ) -> Dict[str, Any]:
        """
        Search for a specific docket number.

        Args:
            session_id: Browser session ID
            docket_number: Docket number (e.g., "1:25-CV-01815")

        Returns:
            Response with status
        """
        response = self.session.post(
            f"{self.base_url}/api/v1/docket/search",
            json={
                "session_id": session_id,
                "docket_number": docket_number
            }
        )
        response.raise_for_status()
        return response.json()

    def create_alert(self, session_id: str) -> Dict[str, Any]:
        """
        Create a docket alert.

        Args:
            session_id: Browser session ID

        Returns:
            Response with status
        """
        response = self.session.post(
            f"{self.base_url}/api/v1/alert/create",
            json={"session_id": session_id}
        )
        response.raise_for_status()
        return response.json()

    def complete_alert_setup(
        self,
        session_id: str,
        alert_name: str,
        alert_description: Optional[str],
        user_email: str,
        frequency: str,
        alert_times: List[str]
    ) -> Dict[str, Any]:
        """
        Complete the alert setup with details.

        Args:
            session_id: Browser session ID
            alert_name: Name of the alert
            alert_description: Description of the alert
            user_email: Email for alert delivery
            frequency: Alert frequency (daily, weekdays, weekly, biweekly, monthly)
            alert_times: Alert times (5am, 12pm, 3pm, 5pm)

        Returns:
            Response with status
        """
        response = self.session.post(
            f"{self.base_url}/api/v1/alert/complete-setup",
            json={
                "session_id": session_id,
                "alert_name": alert_name,
                "alert_description": alert_description,
                "user_email": user_email,
                "frequency": frequency,
                "alert_times": alert_times
            }
        )
        response.raise_for_status()
        return response.json()

    def cleanup_session(self, session_id: str) -> Dict[str, Any]:
        """
        Cleanup a browser session.

        Args:
            session_id: Browser session ID

        Returns:
            Response with status
        """
        response = self.session.post(
            f"{self.base_url}/api/v1/session/cleanup",
            json={"session_id": session_id}
        )
        response.raise_for_status()
        return response.json()

    def list_sessions(self) -> Dict[str, Any]:
        """List all active sessions."""
        response = self.session.get(f"{self.base_url}/api/v1/sessions")
        response.raise_for_status()
        return response.json()
