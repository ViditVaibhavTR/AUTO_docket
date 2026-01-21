"""
Streamlit Chatbot Interface for Docket Alert Automation.
Provides an interactive UI to run the automation workflow.
"""

import streamlit as st
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import settings
from src.automation.browser import BrowserManager
from src.automation.gateway_config import GatewayConfigurator
from src.automation.iac_config import IACConfigurator
from src.automation.westlaw_login import WestLawLogin
from src.automation.docket_selection import DocketSelector
from src.utils.logger import get_logger

logger = get_logger(__name__)

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


def run_automation(include_docket=False):
    """
    Execute the complete Docket Alert automation workflow.
    Returns simple status message and driver for docket selection.
    """
    browser_manager = None

    try:
        # Validate configuration
        settings.validate()

        # Start browser
        browser_manager = BrowserManager()
        driver = browser_manager.start()

        # Navigate to routing page
        browser_manager.login()

        # Configure Gateway Live External
        try:
            gateway_config = GatewayConfigurator()
            gateway_config.configure_gateway(driver)
        except Exception as e:
            pass  # Continue even if gateway fails

        # Configure Infrastructure Access Controls
        iac_config = IACConfigurator()
        iac_config.configure_iac(driver)

        # Login to WestLaw Precision
        westlaw_login = WestLawLogin()
        westlaw_login.login(driver)

        # Keep browser open briefly
        time.sleep(1)

        # Return driver and browser_manager for docket selection if needed
        return "login_success", driver, browser_manager

    except Exception as e:
        logger.error(f"Automation failed: {e}")
        if browser_manager:
            browser_manager.cleanup()
        return f"error: {e}", None, None


def run_docket_selection(driver, browser_manager, category=None, specific_docket=None):
    """
    Run docket category and specific docket selection.
    (Content Types → Dockets has already been clicked)

    Args:
        driver: Selenium WebDriver object
        browser_manager: BrowserManager instance
        category: Selected category (e.g., "Dockets by State")
        specific_docket: Selected specific docket (e.g., "California")
    """
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        wait = WebDriverWait(driver, 10)

        # Click the category
        logger.info(f"Looking for category: {category}")
        category_element = wait.until(
            EC.element_to_be_clickable((By.XPATH, f'//*[contains(text(), "{category}")]'))
        )
        driver.execute_script("arguments[0].click();", category_element)
        logger.info(f"✓ Clicked category: {category}")
        time.sleep(2)

        # Click the specific docket
        logger.info(f"Looking for specific docket: {specific_docket}")
        docket_element = wait.until(
            EC.element_to_be_clickable((By.XPATH, f'//*[contains(text(), "{specific_docket}")]'))
        )
        driver.execute_script("arguments[0].click();", docket_element)
        logger.info(f"✓ Clicked specific docket: {specific_docket}")
        time.sleep(1)

        return "success"

    except Exception as e:
        logger.error(f"Docket selection failed: {e}")
        return f"error: {e}"

    finally:
        # Cleanup
        if browser_manager:
            browser_manager.cleanup()


def main():
    """Main Streamlit application."""

    # Page configuration
    st.set_page_config(
        page_title="Docket Alert Automation Bot",
        page_icon="🤖",
        layout="centered"
    )

    # Custom CSS
    st.markdown("""
        <style>
        .stButton > button {
            width: 100%;
            height: 60px;
            font-size: 20px;
            font-weight: bold;
            border-radius: 10px;
            margin: 10px 0;
        }
        .success-button {
            background-color: #4CAF50 !important;
            color: white !important;
        }
        .danger-button {
            background-color: #f44336 !important;
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Title and header
    st.title("🤖 Docket Alert Automation Bot")
    st.markdown("---")

    # Initialize session state
    if 'started' not in st.session_state:
        st.session_state.started = False
    if 'running' not in st.session_state:
        st.session_state.running = False
    if 'completed' not in st.session_state:
        st.session_state.completed = False
    if 'login_completed' not in st.session_state:
        st.session_state.login_completed = False
    if 'docket_running' not in st.session_state:
        st.session_state.docket_running = False
    if 'driver' not in st.session_state:
        st.session_state.driver = None
    if 'browser_manager' not in st.session_state:
        st.session_state.browser_manager = None
    if 'show_docket_categories' not in st.session_state:
        st.session_state.show_docket_categories = False
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = None
    if 'show_specific_dockets' not in st.session_state:
        st.session_state.show_specific_dockets = False
    if 'selected_docket' not in st.session_state:
        st.session_state.selected_docket = None

    # Main interface
    if not st.session_state.started and not st.session_state.completed and not st.session_state.login_completed:
        # Initial prompt
        st.markdown("### 👋 Welcome to Docket Alert Automation!")
        st.markdown("")
        st.markdown("This bot will automate the following tasks:")
        st.markdown("1. Configure Gateway Live External (set to True)")
        st.markdown("2. Configure Infrastructure Access Controls")
        st.markdown("3. Login to WestLaw Precision")
        st.markdown("")
        st.markdown("### 🚀 Should we get started?")
        st.markdown("")

        # Create two columns for buttons
        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Yes, Let's Go!", key="yes_button", use_container_width=True):
                st.session_state.started = True
                st.session_state.running = True
                st.rerun()

        with col2:
            if st.button("❌ No, Exit", key="no_button", use_container_width=True):
                st.warning("👋 Goodbye! The automation has been cancelled.")
                st.markdown("You can close this window now.")
                st.stop()

    elif st.session_state.started and st.session_state.running:
        # Show automation progress
        st.markdown("### 🔄 Running automation...")
        st.markdown("Please wait...")

        # Run automation
        result, driver, browser_manager = run_automation()

        # Store driver and browser_manager for docket selection
        st.session_state.driver = driver
        st.session_state.browser_manager = browser_manager

        # Mark login as completed
        st.session_state.running = False

        if result == "login_success":
            st.session_state.login_completed = True
            st.session_state.result = result
        else:
            # If error, cleanup and mark as completed
            st.session_state.completed = True
            st.session_state.result = result
            if browser_manager:
                browser_manager.cleanup()

        st.rerun()

    elif st.session_state.login_completed and not st.session_state.show_docket_categories and not st.session_state.docket_running and not st.session_state.completed:
        # Show docket selection prompt
        st.markdown("### ✅ Login completed successfully!")
        st.markdown("")
        st.markdown("### 📋 Should we start with docket selection?")
        st.markdown("")
        st.markdown("This will:")
        st.markdown("- Navigate to Content Types")
        st.markdown("- Select 'Dockets'")
        st.markdown("")

        # Debug info
        logger.info(f"DEBUG: starting_docket_selection = {st.session_state.get('starting_docket_selection', 'NOT SET')}")
        logger.info(f"DEBUG: docket_nav_done = {st.session_state.get('docket_nav_done', 'NOT SET')}")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Yes, Select Docket", key="docket_yes_button", use_container_width=True):
                # Mark that we're starting docket selection
                logger.info("🔵 User clicked 'Yes, Select Docket' button")
                st.session_state.starting_docket_selection = True
                logger.info(f"DEBUG AFTER SET: starting_docket_selection = {st.session_state.starting_docket_selection}")
                st.rerun()

        with col2:
            if st.button("❌ No, Exit", key="docket_no_button", use_container_width=True):
                # Cleanup and exit
                if st.session_state.browser_manager:
                    st.session_state.browser_manager.cleanup()
                st.warning("👋 Goodbye! The browser has been closed.")
                st.markdown("You can close this window now.")
                st.stop()

    # Debug the condition before checking
    logger.info(f"DEBUG CHECK: hasattr starting_docket_selection = {hasattr(st.session_state, 'starting_docket_selection')}")
    if hasattr(st.session_state, 'starting_docket_selection'):
        logger.info(f"DEBUG CHECK: starting_docket_selection value = {st.session_state.starting_docket_selection}")
        logger.info(f"DEBUG CHECK: docket_nav_done = {st.session_state.get('docket_nav_done', False)}")

    if hasattr(st.session_state, 'starting_docket_selection') and st.session_state.starting_docket_selection and not st.session_state.get('docket_nav_done', False):
        # Execute Content Types → Dockets click in backend
        logger.info("🟢 Entering docket navigation block - will click Content Types and Dockets")
        st.markdown("### 🔄 Navigating to Dockets...")
        st.markdown("")
        st.markdown("Please wait while we:")
        st.markdown("1. Click on 'Content Types' tab")
        st.markdown("2. Click on 'Dockets' option")
        st.markdown("")

        # Use a spinner to show progress
        with st.spinner("Clicking Content Types and Dockets..."):
            logger.info("🟡 Inside spinner - about to start clicking")
            try:
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from src.utils.screenshot import ScreenshotManager

                driver = st.session_state.driver
                screenshot_manager = ScreenshotManager()

                # Take before screenshot
                screenshot_manager.capture(driver, "before_content_types_click")
                logger.info("📸 Screenshot: before_content_types_click")

                # Click Content Types tab
                logger.info("Looking for 'Content types' tab...")
                wait = WebDriverWait(driver, 20)

                # Try multiple selectors for Content Types
                content_types_element = None
                selectors = [
                    (By.XPATH, '//*[@id="tab3"]'),
                    (By.XPATH, '//li[contains(text(), "Content types")]'),
                    (By.XPATH, '//li[@role="tab"][contains(text(), "Content types")]')
                ]

                for by, selector in selectors:
                    try:
                        logger.info(f"Trying selector: {selector}")
                        content_types_element = wait.until(EC.presence_of_element_located((by, selector)))
                        logger.info(f"✓ Found Content Types with: {selector}")
                        break
                    except:
                        continue

                if not content_types_element:
                    screenshot_manager.capture_on_error(driver, "content_types_not_found")
                    raise Exception("Content Types tab not found with any selector")

                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", content_types_element)
                time.sleep(0.5)
                screenshot_manager.capture(driver, "before_clicking_content_types")
                driver.execute_script("arguments[0].click();", content_types_element)
                logger.info("✓ Clicked Content Types tab")
                time.sleep(2)
                screenshot_manager.capture(driver, "after_clicking_content_types")
                logger.info("📸 Screenshot: after_clicking_content_types")

                # Click Dockets option
                logger.info("Looking for 'Dockets' option...")

                # Try multiple selectors for Dockets
                dockets_element = None
                docket_selectors = [
                    (By.XPATH, '//span[contains(text(), "Dockets")]'),
                    (By.XPATH, '//div[contains(text(), "Dockets")]'),
                    (By.XPATH, '//a[contains(text(), "Dockets")]'),
                    (By.XPATH, '//*[contains(text(), "Dockets")]')
                ]

                for by, selector in docket_selectors:
                    try:
                        logger.info(f"Trying selector: {selector}")
                        dockets_element = wait.until(EC.element_to_be_clickable((by, selector)))
                        logger.info(f"✓ Found Dockets with: {selector}")
                        break
                    except:
                        continue

                if not dockets_element:
                    screenshot_manager.capture_on_error(driver, "dockets_not_found")
                    raise Exception("Dockets option not found with any selector")

                screenshot_manager.capture(driver, "before_clicking_dockets")
                driver.execute_script("arguments[0].click();", dockets_element)
                logger.info("✓ Clicked Dockets option")
                time.sleep(2)
                screenshot_manager.capture(driver, "after_clicking_dockets")
                logger.info("📸 Screenshot: after_clicking_dockets")

                # Success! Now show category selection
                logger.info("✅ Successfully navigated to Dockets section")
                st.session_state.docket_nav_done = True
                st.session_state.starting_docket_selection = False
                st.session_state.show_docket_categories = True
                st.success("✅ Successfully clicked Content Types and Dockets!")
                time.sleep(1)
                st.rerun()

            except Exception as e:
                logger.error(f"❌ Failed to navigate to Dockets: {e}")
                screenshot_manager.capture_on_error(driver, "docket_navigation_failed")
                st.session_state.completed = True
                st.session_state.result = f"error: Failed to navigate to Dockets - {e}"
                if st.session_state.browser_manager:
                    st.session_state.browser_manager.cleanup()
                st.rerun()

    elif st.session_state.show_docket_categories and not st.session_state.selected_category:
        # Show docket category selection
        st.markdown("### 📂 Select Docket Category")
        st.markdown("")
        st.markdown("Please choose a category:")
        st.markdown("")

        # Display category buttons in a grid
        categories = list(DOCKET_CATEGORIES.keys())

        for i in range(0, len(categories), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j < len(categories):
                    category = categories[i + j]
                    with col:
                        if st.button(f"📁 {category}", key=f"cat_{i+j}", use_container_width=True):
                            st.session_state.selected_category = category
                            st.session_state.show_specific_dockets = True
                            st.rerun()

        st.markdown("")
        st.markdown("---")

        # Back button
        if st.button("⬅️ Back", key="back_from_categories", use_container_width=False):
            st.session_state.show_docket_categories = False
            st.rerun()

    elif st.session_state.show_specific_dockets and st.session_state.selected_category:
        # Show specific docket options for selected category
        st.markdown(f"### 📋 {st.session_state.selected_category}")
        st.markdown("")
        st.markdown("Please select a specific docket:")
        st.markdown("")

        # Get docket options for selected category
        docket_options = DOCKET_CATEGORIES[st.session_state.selected_category]

        # Display docket option buttons in a grid
        for i in range(0, len(docket_options), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j < len(docket_options):
                    docket = docket_options[i + j]
                    with col:
                        if st.button(f"📄 {docket}", key=f"docket_{i+j}", use_container_width=True):
                            st.session_state.selected_docket = docket
                            st.session_state.docket_running = True
                            st.rerun()

        st.markdown("")
        st.markdown("---")

        # Back button
        if st.button("⬅️ Back to Categories", key="back_from_dockets", use_container_width=False):
            st.session_state.show_specific_dockets = False
            st.session_state.selected_category = None
            st.rerun()

    elif st.session_state.docket_running and not st.session_state.completed:
        # Show docket selection progress
        st.markdown("### 🔄 Selecting docket...")
        st.markdown("")
        st.markdown(f"**Category:** {st.session_state.selected_category}")
        st.markdown(f"**Docket:** {st.session_state.selected_docket}")
        st.markdown("")
        st.markdown("Please wait...")

        # Run docket selection with category and specific docket
        result = run_docket_selection(
            st.session_state.driver,
            st.session_state.browser_manager,
            category=st.session_state.selected_category,
            specific_docket=st.session_state.selected_docket
        )

        # Mark as completed
        st.session_state.docket_running = False
        st.session_state.completed = True
        st.session_state.result = result
        st.rerun()

    elif st.session_state.completed:
        # Show completion screen
        if hasattr(st.session_state, 'result') and st.session_state.result == "success":
            st.markdown("### ✅ Task done")
            st.markdown("")
            if st.session_state.selected_category and st.session_state.selected_docket:
                st.markdown(f"**Category:** {st.session_state.selected_category}")
                st.markdown(f"**Selected Docket:** {st.session_state.selected_docket}")
        else:
            st.markdown("### ❌ Task failed")
            if hasattr(st.session_state, 'result'):
                st.error(st.session_state.result)

        st.markdown("")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Run Again", key="restart_button", use_container_width=True):
                st.session_state.started = False
                st.session_state.running = False
                st.session_state.completed = False
                st.session_state.login_completed = False
                st.session_state.docket_running = False
                st.session_state.driver = None
                st.session_state.browser_manager = None
                st.session_state.show_docket_categories = False
                st.session_state.selected_category = None
                st.session_state.show_specific_dockets = False
                st.session_state.selected_docket = None
                if hasattr(st.session_state, 'result'):
                    delattr(st.session_state, 'result')
                st.rerun()

        with col2:
            if st.button("🚪 Exit", key="exit_button", use_container_width=True):
                st.success("👋 Goodbye!")
                st.markdown("You can close this window now.")
                st.stop()


if __name__ == "__main__":
    main()
