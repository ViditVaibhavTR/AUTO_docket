"""
FastAPI Application for Docket Alert Automation.
Provides REST API endpoints for the automation workflow.
"""

import sys
import uuid
from pathlib import Path
from typing import Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.automation.browser import BrowserManager
from src.automation.gateway_config import GatewayConfigurator
from src.automation.iac_config import IACConfigurator
from src.automation.westlaw_login import WestLawLogin
from src.automation.docket_selection import DocketSelector
from src.utils.logger import get_logger
from api.schemas import (
    AutomationStartRequest,
    AutomationStartResponse,
    DocketSelectionRequest,
    DocketSelectionResponse,
    DistrictSelectionRequest,
    DistrictSelectionResponse,
    DocketSearchRequest,
    DocketSearchResponse,
    CreateAlertRequest,
    CreateAlertResponse,
    CompleteAlertSetupRequest,
    CompleteAlertSetupResponse,
    SessionCleanupRequest,
    SessionCleanupResponse,
    HealthCheckResponse,
    DocketCategoriesResponse,
    StatesResponse,
    DistrictsResponse,
)

logger = get_logger(__name__)

# Global session storage (in production, use Redis or database)
browser_sessions: Dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app."""
    logger.info("Starting Docket Alert Automation API")
    yield
    logger.info("Shutting down Docket Alert Automation API")
    # Cleanup all browser sessions
    for session_id in list(browser_sessions.keys()):
        try:
            session = browser_sessions[session_id]
            if session.get("browser_manager"):
                session["browser_manager"].cleanup()
            del browser_sessions[session_id]
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")


# Initialize FastAPI app
app = FastAPI(
    title="Docket Alert Automation API",
    description="REST API for automating docket alert creation on WestLaw Precision",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Hierarchical docket menu structure
DOCKET_CATEGORIES = {
    "Federal Dockets by Court": [
        "U.S. Supreme Court",
        "U.S. Courts of Appeals",
        "Federal District Courts",
        "Federal Bankruptcy Courts",
        "U.S. Tax Court",
        "U.S. Court of Federal Claims",
        "U.S. Court of International Trade",
        "U.S. Judicial Panel on Multidistrict Litigation"
    ],
    "Federal Dockets by Agency": [
        "Copyright Claims Board",
        "Patent Trial & Appeal Board",
        "Securities & Exchange Commission",
        "Trademark Trial & Appeal Board",
        "U.S. International Trade Commission"
    ],
    "Dockets by State": [
        "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
        "Connecticut", "Delaware", "District of Columbia", "Florida", "Georgia",
        "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
        "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
        "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
        "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota",
        "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
        "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia",
        "Washington", "West Virginia", "Wisconsin", "Wyoming"
    ],
    "Dockets by Territory": [
        "Guam",
        "Northern Mariana Islands",
        "Puerto Rico",
        "Virgin Islands"
    ],
    "International": [
        "United Kingdom"
    ],
    "Dockets by Topic": [
        "Admiralty & Maritime",
        "Business & Commercial",
        "Environmental Law",
        "Family Law",
        "Foreign Corrupt Practices Act",
        "Immigration",
        "Insurance",
        "Intellectual Property",
        "Labor & Employment",
        "Real Property",
        "Securities (Federal)",
        "Tax"
    ]
}


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


@app.post("/api/v1/automation/start", response_model=AutomationStartResponse)
async def start_automation(request: AutomationStartRequest):
    """
    Start the automation process: login and configure gateway/IAC.

    Returns a session ID for subsequent requests.
    """
    browser_manager = None
    session_id = str(uuid.uuid4())

    try:
        logger.info(f"Starting automation for session {session_id}")

        # Validate configuration
        settings.validate()

        # Start browser
        browser_manager = BrowserManager()
        driver = browser_manager.start()

        # Navigate to routing page
        browser_manager.login()

        # Configure Gateway Live External (allow failures)
        try:
            gateway_config = GatewayConfigurator()
            gateway_config.configure_gateway(driver)
        except Exception as e:
            logger.warning(f"Gateway configuration failed (continuing): {e}")

        # Configure Infrastructure Access Controls
        iac_config = IACConfigurator()
        iac_config.configure_iac(driver)

        # Login to WestLaw Precision
        westlaw_login = WestLawLogin()
        westlaw_login.login(driver)

        # Store session
        browser_sessions[session_id] = {
            "driver": driver,
            "browser_manager": browser_manager,
            "state": "logged_in"
        }

        logger.info(f"Automation started successfully for session {session_id}")

        return AutomationStartResponse(
            status="login_success",
            message="Successfully logged in and configured",
            session_id=session_id
        )

    except Exception as e:
        logger.error(f"Automation failed for session {session_id}: {e}")
        if browser_manager:
            browser_manager.cleanup()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Automation failed: {str(e)}"
        )


@app.post("/api/v1/docket/select", response_model=DocketSelectionResponse)
async def select_docket(request: DocketSelectionRequest):
    """
    Select a docket category and specific docket.

    This handles: Content Types → Dockets → Category → Specific Docket
    """
    if request.session_id not in browser_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    session = browser_sessions[request.session_id]
    driver = session["driver"]

    try:
        logger.info(f"Selecting docket for session {request.session_id}")
        logger.info(f"Category: {request.category}, Docket: {request.specific_docket}")

        docket_selector = DocketSelector()
        success = docket_selector.select_docket(
            driver,
            category=request.category,
            specific_docket=request.specific_docket
        )

        if success:
            session["state"] = "docket_selected"
            return DocketSelectionResponse(
                status="success",
                message=f"Successfully selected {request.category} → {request.specific_docket}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Docket selection failed"
            )

    except Exception as e:
        logger.error(f"Docket selection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Docket selection failed: {str(e)}"
        )


@app.post("/api/v1/district/select", response_model=DistrictSelectionResponse)
async def select_district(request: DistrictSelectionRequest):
    """Select a district for the chosen state."""
    if request.session_id not in browser_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    session = browser_sessions[request.session_id]
    driver = session["driver"]

    try:
        logger.info(f"Selecting district for session {request.session_id}")
        logger.info(f"State: {request.state}, District: {request.district}")

        # Import here to avoid circular imports
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from src.utils.screenshot import ScreenshotManager
        import time

        screenshot_manager = ScreenshotManager()
        wait = WebDriverWait(driver, 15)

        # Map district names to their exact href paths
        district_href_map = {
            "Central District": "CaliforniaFederalDistrictCourtDocketsCentralDistrict",
            "Eastern District": "CaliforniaFederalDistrictCourtDocketsEasternDistrict",
            "Northern District": "CaliforniaFederalDistrictCourtDocketsNorthernDistrict",
            "Southern District": "CaliforniaFederalDistrictCourtDocketsSouthernDistrict"
        }

        district_href = district_href_map.get(request.district, "")

        district_selectors = []
        if district_href:
            district_selectors.extend([
                (By.XPATH, f'//a[contains(@href, "{district_href}")]'),
                (By.CSS_SELECTOR, f'a[href*="{district_href}"]'),
            ])

        district_selectors.extend([
            (By.XPATH, f'//a[text()="{request.district}"]'),
            (By.XPATH, f'//a[contains(text(), "{request.district}")]'),
        ])

        district_element = None
        for by_type, selector in district_selectors:
            try:
                district_element = wait.until(
                    EC.element_to_be_clickable((by_type, selector))
                )
                logger.info(f"Found district with: {by_type}={selector}")
                break
            except:
                continue

        if not district_element:
            raise Exception(f"Cannot find district: {request.district}")

        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", district_element)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", district_element)
        logger.info(f"Clicked district: {request.district}")
        time.sleep(2)

        session["state"] = "district_selected"

        return DistrictSelectionResponse(
            status="success",
            message=f"Successfully selected district: {request.district}"
        )

    except Exception as e:
        logger.error(f"District selection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"District selection failed: {str(e)}"
        )


@app.post("/api/v1/docket/search", response_model=DocketSearchResponse)
async def search_docket(request: DocketSearchRequest):
    """Search for a specific docket number."""
    if request.session_id not in browser_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    session = browser_sessions[request.session_id]
    driver = session["driver"]

    try:
        logger.info(f"Searching docket for session {request.session_id}")
        logger.info(f"Docket Number: {request.docket_number}")

        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time

        wait = WebDriverWait(driver, 5)

        # Find docket number input field
        input_selectors = [
            (By.ID, "co_search_advancedSearch_DN"),
            (By.NAME, "co_search_advancedSearch_DN"),
        ]

        input_element = None
        for by, selector in input_selectors:
            try:
                input_element = wait.until(
                    EC.presence_of_element_located((by, selector))
                )
                break
            except:
                continue

        if not input_element:
            raise Exception("Cannot find docket number input field")

        # Enter docket number
        input_element.clear()
        time.sleep(0.3)
        input_element.send_keys(request.docket_number)
        time.sleep(0.5)

        # Find and click search button
        search_selectors = [
            (By.ID, "searchButton"),
            (By.XPATH, '//button[@id="searchButton"]'),
        ]

        search_button = None
        for by, selector in search_selectors:
            try:
                search_button = wait.until(
                    EC.element_to_be_clickable((by, selector))
                )
                break
            except:
                continue

        if not search_button:
            raise Exception("Cannot find search button")

        search_button.click()
        time.sleep(2)

        session["state"] = "docket_searched"

        return DocketSearchResponse(
            status="success",
            message=f"Successfully searched for docket: {request.docket_number}"
        )

    except Exception as e:
        logger.error(f"Docket search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Docket search failed: {str(e)}"
        )


@app.post("/api/v1/alert/create", response_model=CreateAlertResponse)
async def create_alert(request: CreateAlertRequest):
    """
    Create a docket alert by clicking the notification icon and selecting 'Create Docket Alert'.
    """
    if request.session_id not in browser_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    session = browser_sessions[request.session_id]
    driver = session["driver"]

    try:
        logger.info(f"Creating alert for session {request.session_id}")

        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time

        wait = WebDriverWait(driver, 10)
        time.sleep(3)

        # Find and click "Create Alert menu" button
        notification_selectors = [
            (By.ID, 'co_search_alertMenuLink'),
            (By.XPATH, '//button[@id="co_search_alertMenuLink"]'),
        ]

        notification_icon = None
        for by, selector in notification_selectors:
            try:
                notification_icon = wait.until(
                    EC.element_to_be_clickable((by, selector))
                )
                break
            except:
                continue

        if not notification_icon:
            raise Exception("Cannot find 'Create Alert menu' button")

        notification_icon.click()
        time.sleep(2)

        # Find and click "Create Docket Alert" option
        create_alert_selectors = [
            (By.XPATH, '//a[contains(text(), "Create Docket Alert")]'),
            (By.XPATH, '//button[contains(text(), "Create Docket Alert")]'),
        ]

        create_alert_button = None
        for by, selector in create_alert_selectors:
            try:
                create_alert_button = wait.until(
                    EC.element_to_be_clickable((by, selector))
                )
                break
            except:
                continue

        if not create_alert_button:
            raise Exception("Cannot find 'Create Docket Alert' option")

        create_alert_button.click()
        time.sleep(3)

        session["state"] = "alert_created"

        return CreateAlertResponse(
            status="success",
            message="Successfully clicked 'Create Docket Alert'"
        )

    except Exception as e:
        logger.error(f"Create alert failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Create alert failed: {str(e)}"
        )


@app.post("/api/v1/alert/complete-setup", response_model=CompleteAlertSetupResponse)
async def complete_alert_setup(request: CompleteAlertSetupRequest):
    """
    Complete the alert setup by filling all form fields and saving.
    """
    if request.session_id not in browser_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    session = browser_sessions[request.session_id]
    driver = session["driver"]

    try:
        logger.info(f"Completing alert setup for session {request.session_id}")

        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait, Select
        from selenium.webdriver.support import expected_conditions as EC
        import time

        wait = WebDriverWait(driver, 10)
        time.sleep(2)

        # Fill alert name
        name_input = wait.until(
            EC.presence_of_element_located((By.ID, "optionsAlertName"))
        )
        name_input.clear()
        name_input.send_keys(request.alert_name)
        time.sleep(0.5)

        # Fill description if provided
        if request.alert_description:
            description_input = wait.until(
                EC.presence_of_element_located((By.ID, "optionsAlertDescription"))
            )
            description_input.clear()
            description_input.send_keys(request.alert_description)
            time.sleep(0.5)

        # Click Continue (Basics)
        continue_button = wait.until(
            EC.element_to_be_clickable((By.ID, "co_button_continue_Basics"))
        )
        continue_button.click()
        time.sleep(3)

        # Click "All Content" tab
        all_content_tab = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//button[@role="tab"][@aria-controls="All_Content"]'))
        )
        all_content_tab.click()
        time.sleep(1)

        # Click Continue (Select Content)
        continue_content_button = wait.until(
            EC.element_to_be_clickable((By.ID, "co_button_continue_Content"))
        )
        continue_content_button.click()
        time.sleep(3)

        # Click "Alert me to all new filings" radio
        new_filings_radio = wait.until(
            EC.element_to_be_clickable((By.ID, "co_search_alertMeToNewFilings"))
        )
        new_filings_radio.click()
        time.sleep(1)

        # Click Continue (Enter Search Terms)
        continue_search_button = wait.until(
            EC.element_to_be_clickable((By.ID, "co_button_continue_Search"))
        )
        continue_search_button.click()
        time.sleep(3)

        # Fill email
        email_container = wait.until(
            EC.element_to_be_clickable((By.ID, "coid_contacts_addedContactsInput_co_collaboratorWidget"))
        )
        email_container.click()
        time.sleep(1)

        email_input = wait.until(
            EC.element_to_be_clickable((By.ID, "coid_contacts_autoSuggest_input"))
        )
        email_input.clear()
        email_input.send_keys(request.user_email)
        time.sleep(1)
        email_input.send_keys(Keys.ENTER)
        time.sleep(2)

        # Click Continue (Customize delivery)
        continue_delivery_button = wait.until(
            EC.element_to_be_clickable((By.ID, "co_button_continue_Delivery"))
        )
        continue_delivery_button.click()
        time.sleep(3)

        # Select frequency
        frequency_dropdown = wait.until(
            EC.presence_of_element_located((By.ID, "frequencySelect"))
        )
        select = Select(frequency_dropdown)
        select.select_by_value(request.frequency)
        time.sleep(1)

        # Check alert times
        time_checkbox_ids = {
            '5am': 'amExecutionTime5',
            '12pm': 'pmExecutionTime12',
            '3pm': 'pmExecutionTime3',
            '5pm': 'pmExecutionTime5'
        }

        for time_label in request.alert_times:
            if time_label in time_checkbox_ids:
                checkbox_id = time_checkbox_ids[time_label]
                try:
                    checkbox = wait.until(
                        EC.presence_of_element_located((By.ID, checkbox_id))
                    )
                    if not checkbox.is_selected():
                        checkbox.click()
                    time.sleep(0.3)
                except Exception as e:
                    logger.warning(f"Could not check {time_label} checkbox: {e}")

        # Click "Save alert" button
        save_alert_button = wait.until(
            EC.element_to_be_clickable((By.ID, "co_button_saveAlert"))
        )
        save_alert_button.click()
        time.sleep(3)

        session["state"] = "alert_setup_complete"

        return CompleteAlertSetupResponse(
            status="success",
            message="Alert setup completed successfully"
        )

    except Exception as e:
        logger.error(f"Complete alert setup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Complete alert setup failed: {str(e)}"
        )


@app.post("/api/v1/session/cleanup", response_model=SessionCleanupResponse)
async def cleanup_session(request: SessionCleanupRequest):
    """Cleanup a browser session."""
    if request.session_id not in browser_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    try:
        session = browser_sessions[request.session_id]
        browser_manager = session.get("browser_manager")

        if browser_manager:
            browser_manager.cleanup()

        del browser_sessions[request.session_id]

        return SessionCleanupResponse(
            status="success",
            message=f"Session {request.session_id} cleaned up successfully"
        )

    except Exception as e:
        logger.error(f"Session cleanup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session cleanup failed: {str(e)}"
        )


@app.get("/api/v1/sessions")
async def list_sessions():
    """List all active browser sessions."""
    return {
        "active_sessions": list(browser_sessions.keys()),
        "count": len(browser_sessions)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
