"""
Health check and informational API endpoints.
"""

from api.app import app
from api.constants import DOCKET_CATEGORIES
from models.schemas import (
    HealthCheckResponse,
    DocketCategoriesResponse,
    StatesResponse,
    DistrictsResponse,
)


@app.get("/", response_model=HealthCheckResponse)
async def root():
    """Root endpoint - health check."""
    return HealthCheckResponse(
        status="ok",
        version="1.0.0",
        message="Docket Alert Automation API is running"
    )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        message="API is operational"
    )


@app.get("/api/v1/docket-categories", response_model=DocketCategoriesResponse)
async def get_docket_categories():
    """Get available docket categories."""
    return DocketCategoriesResponse(categories=DOCKET_CATEGORIES)


@app.get("/api/v1/states", response_model=StatesResponse)
async def get_states():
    """Get available states (limited to 3 for demo)."""
    states = ["California", "New York", "Texas"]
    return StatesResponse(states=states)


@app.get("/api/v1/districts", response_model=DistrictsResponse)
async def get_districts(state: str):
    """Get available districts for a state."""
    # For demo purposes, returning standard districts
    districts = ["Central District", "Eastern District", "Northern District", "Southern District"]
    return DistrictsResponse(state=state, districts=districts)
