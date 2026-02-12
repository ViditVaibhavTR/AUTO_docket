"""
API Request/Response schemas using Pydantic models.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


class AutomationStartRequest(BaseModel):
    """Request to start automation process."""
    include_docket: bool = Field(default=False, description="Include docket selection in automation")


class AutomationStartResponse(BaseModel):
    """Response from automation start."""
    status: str = Field(..., description="Status: login_success or error")
    message: Optional[str] = Field(None, description="Additional message or error details")
    session_id: Optional[str] = Field(None, description="Session ID for browser instance")


class DocketSelectionRequest(BaseModel):
    """Request to select a docket."""
    session_id: str = Field(..., description="Browser session ID")
    category: str = Field(..., description="Docket category (e.g., 'Dockets by State')")
    specific_docket: str = Field(..., description="Specific docket name (e.g., 'California')")


class DocketSelectionResponse(BaseModel):
    """Response from docket selection."""
    status: str = Field(..., description="Status: success or error")
    message: Optional[str] = Field(None, description="Additional message or error details")


class DistrictSelectionRequest(BaseModel):
    """Request to select a district."""
    session_id: str = Field(..., description="Browser session ID")
    state: str = Field(..., description="State name")
    district: str = Field(..., description="District name (e.g., 'Central District')")


class DistrictSelectionResponse(BaseModel):
    """Response from district selection."""
    status: str = Field(..., description="Status: success or error")
    message: Optional[str] = Field(None, description="Additional message or error details")


class DocketSearchRequest(BaseModel):
    """Request to search for a docket number."""
    session_id: str = Field(..., description="Browser session ID")
    docket_number: str = Field(..., description="Docket number (e.g., '1:25-CV-01815')")


class DocketSearchResponse(BaseModel):
    """Response from docket search."""
    status: str = Field(..., description="Status: success or error")
    message: Optional[str] = Field(None, description="Additional message or error details")


class CreateAlertRequest(BaseModel):
    """Request to create a docket alert."""
    session_id: str = Field(..., description="Browser session ID")


class CreateAlertResponse(BaseModel):
    """Response from create alert action."""
    status: str = Field(..., description="Status: success or error")
    message: Optional[str] = Field(None, description="Additional message or error details")


class CompleteAlertSetupRequest(BaseModel):
    """Request to complete alert setup with details."""
    session_id: str = Field(..., description="Browser session ID")
    alert_name: str = Field(..., description="Name of the alert")
    alert_description: Optional[str] = Field(None, description="Description of the alert")
    user_email: str = Field(..., description="Email for alert delivery")
    frequency: str = Field(..., description="Alert frequency: daily, weekdays, weekly, biweekly, monthly")
    alert_times: List[str] = Field(..., description="Alert times: 5am, 12pm, 3pm, 5pm")


class CompleteAlertSetupResponse(BaseModel):
    """Response from complete alert setup."""
    status: str = Field(..., description="Status: success or error")
    message: Optional[str] = Field(None, description="Additional message or error details")


class SessionCleanupRequest(BaseModel):
    """Request to cleanup a browser session."""
    session_id: str = Field(..., description="Browser session ID to cleanup")


class SessionCleanupResponse(BaseModel):
    """Response from session cleanup."""
    status: str = Field(..., description="Status: success or error")
    message: Optional[str] = Field(None, description="Additional message or error details")


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="API status")
    version: str = Field(..., description="API version")
    message: str = Field(..., description="Health check message")


class DocketCategoriesResponse(BaseModel):
    """Response with available docket categories."""
    categories: dict = Field(..., description="Dictionary of docket categories and their options")


class StatesResponse(BaseModel):
    """Response with available states."""
    states: List[str] = Field(..., description="List of available states")


class DistrictsResponse(BaseModel):
    """Response with available districts for a state."""
    state: str = Field(..., description="State name")
    districts: List[str] = Field(..., description="List of available districts")
