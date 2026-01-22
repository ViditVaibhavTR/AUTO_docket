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
    Run docket category and specific docket selection using DocketSelector.
    This handles the complete flow: Content Types → Dockets → Category → Specific Docket

    Args:
        driver: Selenium WebDriver object
        browser_manager: BrowserManager instance
        category: Selected category (e.g., "Dockets by State")
        specific_docket: Selected specific docket (e.g., "California")
    """
    try:
        logger.info("=" * 60)
        logger.info("STARTING DOCKET SELECTION TEST")
        logger.info(f"Category: {category}")
        logger.info(f"Specific Docket: {specific_docket}")
        logger.info("=" * 60)

        # Use DocketSelector to handle the entire flow
        docket_selector = DocketSelector()
        success = docket_selector.select_docket(
            driver,
            category=category,
            specific_docket=specific_docket
        )

        if success:
            logger.info("=" * 60)
            logger.info("✓✓✓ DOCKET SELECTION COMPLETED SUCCESSFULLY ✓✓✓")
            logger.info(f"Selected: {category} → {specific_docket}")
            logger.info("=" * 60)
            return "success"
        else:
            logger.error("Docket selection returned False")
            return "error: Docket selection failed"

    except Exception as e:
        logger.error(f"❌ Docket selection failed: {e}")
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
    if 'navigate_to_dockets' not in st.session_state:
        st.session_state.navigate_to_dockets = False
    if 'dockets_nav_complete' not in st.session_state:
        st.session_state.dockets_nav_complete = False
    if 'state_selected' not in st.session_state:
        st.session_state.state_selected = False
    if 'show_district_selection' not in st.session_state:
        st.session_state.show_district_selection = False
    if 'selected_district' not in st.session_state:
        st.session_state.selected_district = None
    if 'district_running' not in st.session_state:
        st.session_state.district_running = False

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

    elif st.session_state.login_completed and not st.session_state.show_docket_categories and not st.session_state.docket_running and not st.session_state.completed and not st.session_state.get('navigate_to_dockets', False) and not st.session_state.get('show_district_selection', False):
        # Show docket selection prompt
        st.markdown("### ✅ Login completed successfully!")
        st.markdown("")
        st.markdown("### 📋 Should we start with docket selection?")
        st.markdown("")
        st.markdown("This will:")
        st.markdown("- Navigate to Content Types")
        st.markdown("- Select 'Dockets'")
        st.markdown("")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Yes, Select Docket", key="docket_yes_button", use_container_width=True):
                # Trigger Content Types → Dockets navigation
                logger.info("🔵 User clicked 'Yes, Select Docket' button")
                st.session_state.navigate_to_dockets = True
                st.rerun()

        with col2:
            if st.button("❌ No, Exit", key="docket_no_button", use_container_width=True):
                # Cleanup and exit
                if st.session_state.browser_manager:
                    st.session_state.browser_manager.cleanup()
                st.warning("👋 Goodbye! The browser has been closed.")
                st.markdown("You can close this window now.")
                st.stop()

    # Phase 1: Execute Content Types → Dockets navigation
    elif st.session_state.get('navigate_to_dockets', False) and not st.session_state.get('dockets_nav_complete', False):
        st.markdown("### 🔄 Navigating to Dockets...")
        st.markdown("")
        st.markdown("Please wait while we:")
        st.markdown("1. Click on 'Content Types' tab")
        st.markdown("2. Click on 'Dockets' option")
        st.markdown("")

        with st.spinner("Executing Content Types → Dockets..."):
            try:
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from src.utils.screenshot import ScreenshotManager

                driver = st.session_state.driver
                screenshot_manager = ScreenshotManager()
                wait = WebDriverWait(driver, 20)

                # Take before screenshot
                screenshot_manager.capture(driver, "before_content_types_click")
                logger.info("📸 Screenshot: before_content_types_click")

                # Click Content Types tab
                logger.info("Looking for 'Content types' tab...")
                content_types_selectors = [
                    (By.XPATH, '//*[@id="tab3"]'),
                    (By.XPATH, '//li[contains(text(), "Content types")]'),
                    (By.XPATH, '//li[@role="tab"][contains(text(), "Content types")]')
                ]

                content_types_element = None
                for by, selector in content_types_selectors:
                    try:
                        logger.info(f"Trying selector: {selector}")
                        content_types_element = wait.until(EC.presence_of_element_located((by, selector)))
                        logger.info(f"✓ Found Content Types with: {selector}")
                        break
                    except:
                        continue

                if not content_types_element:
                    screenshot_manager.capture_on_error(driver, "content_types_not_found")
                    raise Exception("Content Types tab not found")

                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", content_types_element)
                time.sleep(0.5)
                screenshot_manager.capture(driver, "before_clicking_content_types")
                driver.execute_script("arguments[0].click();", content_types_element)
                logger.info("✓ Clicked Content Types tab")
                time.sleep(2)
                screenshot_manager.capture(driver, "after_clicking_content_types")

                # Click Dockets option
                logger.info("Looking for 'Dockets' option...")
                docket_selectors = [
                    (By.XPATH, '//span[contains(text(), "Dockets")]'),
                    (By.XPATH, '//div[contains(text(), "Dockets")]'),
                    (By.XPATH, '//a[contains(text(), "Dockets")]'),
                    (By.XPATH, '//*[contains(text(), "Dockets")]')
                ]

                dockets_element = None
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
                    raise Exception("Dockets option not found")

                screenshot_manager.capture(driver, "before_clicking_dockets")
                driver.execute_script("arguments[0].click();", dockets_element)
                logger.info("✓ Clicked Dockets option")
                time.sleep(2)
                screenshot_manager.capture(driver, "after_clicking_dockets")

                # Success! Mark as complete and show state selection
                logger.info("✅ Successfully navigated to Dockets section")
                st.session_state.dockets_nav_complete = True
                st.session_state.navigate_to_dockets = False
                st.session_state.show_docket_categories = True
                st.success("✅ Successfully navigated to Content Types → Dockets!")
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

    elif st.session_state.show_docket_categories:
        # Show state dockets directly - only 3 states
        st.markdown("### 📂 Dockets by State")
        st.markdown("")
        st.markdown("Please select a state:")
        st.markdown("")

        # Only show 3 specific states
        states = ["California", "New York", "Texas"]

        # Display state buttons
        for state in states:
            if st.button(f"📄 {state}", key=f"state_{state}", use_container_width=True):
                logger.info(f"🔵 User selected state: {state}")
                st.session_state.selected_docket = state
                st.session_state.show_docket_categories = False  # Reset this flag so docket_running block executes
                st.session_state.docket_running = True
                st.rerun()

        st.markdown("")
        st.markdown("---")

        # Back button
        if st.button("⬅️ Back", key="back_from_states", use_container_width=False):
            st.session_state.show_docket_categories = False
            st.rerun()

    elif st.session_state.docket_running and not st.session_state.completed:
        # Show docket selection progress - Phase 2: Only Dockets by State → California
        logger.info(f"🟢 PHASE 2: Selecting {st.session_state.selected_docket}")
        st.markdown("### 🔄 Selecting state docket...")
        st.markdown("")
        st.markdown(f"**State:** {st.session_state.selected_docket}")
        st.markdown("")
        st.markdown("Please wait while we:")
        st.markdown(f"1. Click 'Dockets by State'")
        st.markdown(f"2. Click '{st.session_state.selected_docket}'")
        st.markdown("")

        # Execute only the category and state selection (Content Types → Dockets already done)
        logger.info(f"🟡 Executing Dockets by State → {st.session_state.selected_docket}")
        with st.spinner(f"Navigating: Dockets by State → {st.session_state.selected_docket}..."):
            try:
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from src.utils.screenshot import ScreenshotManager

                driver = st.session_state.driver
                screenshot_manager = ScreenshotManager()
                wait = WebDriverWait(driver, 15)

                # Click "Dockets by State" category
                logger.info("Looking for 'Dockets by State' category...")
                screenshot_manager.capture(driver, "before_clicking_dockets_by_state")

                category_element = wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//*[contains(text(), "Dockets by State")]'))
                )
                logger.info("✓ Found 'Dockets by State'")
                driver.execute_script("arguments[0].click();", category_element)
                logger.info("✓ Clicked 'Dockets by State'")
                time.sleep(2)
                screenshot_manager.capture(driver, "after_clicking_dockets_by_state")

                # Wait for state list to load
                logger.info("Waiting for state list to load...")
                time.sleep(3)

                # Click the specific state using multiple selectors
                logger.info(f"Looking for state: {st.session_state.selected_docket}")
                screenshot_manager.capture(driver, "before_searching_state")

                state_selectors = [
                    f'//a[text()="{st.session_state.selected_docket}"]',
                    f'//a[contains(text(), "{st.session_state.selected_docket}")]',
                    f'//*[@href and contains(text(), "{st.session_state.selected_docket}")]',
                    f'//*[text()="{st.session_state.selected_docket}"]',
                    f'//*[contains(text(), "{st.session_state.selected_docket}")]'
                ]

                state_element = None
                for selector in state_selectors:
                    try:
                        logger.info(f"Trying state selector: {selector}")
                        state_element = wait.until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        logger.info(f"✓ Found state with: {selector}")
                        break
                    except Exception as e:
                        logger.debug(f"Selector failed: {selector}")
                        continue

                if not state_element:
                    screenshot_manager.capture_on_error(driver, "state_not_found")
                    raise Exception(f"Cannot find state: {st.session_state.selected_docket}")

                logger.info(f"✓ Found state: {st.session_state.selected_docket}")

                # Scroll into view and click
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", state_element)
                time.sleep(0.5)
                screenshot_manager.capture(driver, "before_clicking_state")
                driver.execute_script("arguments[0].click();", state_element)
                logger.info(f"✓ Clicked state: {st.session_state.selected_docket}")
                time.sleep(2)
                screenshot_manager.capture(driver, "after_clicking_state")

                # Success! Now show district selection
                logger.info("✅ State selection completed successfully!")
                st.session_state.docket_running = False
                st.session_state.state_selected = True  # Mark state selection complete
                st.session_state.show_district_selection = True  # Show district UI
                st.success(f"✅ Successfully selected {st.session_state.selected_docket}!")
                time.sleep(1)
                st.rerun()

            except Exception as e:
                logger.error(f"❌ State selection failed: {e}")
                screenshot_manager.capture_on_error(driver, "state_selection_error")
                st.session_state.completed = True
                st.session_state.result = f"error: {e}"
                if st.session_state.browser_manager:
                    st.session_state.browser_manager.cleanup()
                st.rerun()

    elif st.session_state.show_district_selection and not st.session_state.district_running and not st.session_state.completed:
        # Show district selection UI
        st.markdown(f"### 📂 {st.session_state.selected_docket} - Select District")
        st.markdown("")
        st.markdown("Please select a district:")
        st.markdown("")

        # Show 4 district options
        districts = ["Eastern District", "Northern District", "Southern District", "Western District"]

        # Display district buttons
        for district in districts:
            if st.button(f"📄 {district}", key=f"district_{district.replace(' ', '_')}", use_container_width=True):
                logger.info(f"🔵 User selected district: {district}")
                st.session_state.selected_district = district
                st.session_state.show_district_selection = False
                st.session_state.district_running = True
                st.rerun()

        st.markdown("")
        st.markdown("---")

        # Back button
        if st.button("⬅️ Back", key="back_from_districts", use_container_width=False):
            st.session_state.show_district_selection = False
            st.session_state.show_docket_categories = True
            st.rerun()

    elif st.session_state.district_running and not st.session_state.completed:
        # Show district selection progress - Phase 3: Only District selection
        logger.info(f"🟢 PHASE 3: Selecting {st.session_state.selected_district}")
        st.markdown("### 🔄 Selecting district...")
        st.markdown("")
        st.markdown(f"**State:** {st.session_state.selected_docket}")
        st.markdown(f"**District:** {st.session_state.selected_district}")
        st.markdown("")
        st.markdown("Please wait while we:")
        st.markdown(f"1. Click '{st.session_state.selected_district}'")
        st.markdown("")

        # Execute only the district selection (State already clicked in Phase 2)
        logger.info(f"🟡 Executing District Selection → {st.session_state.selected_district}")
        with st.spinner(f"Selecting: {st.session_state.selected_district}..."):
            try:
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from src.utils.screenshot import ScreenshotManager

                driver = st.session_state.driver
                screenshot_manager = ScreenshotManager()
                wait = WebDriverWait(driver, 15)

                # Wait for district options to be visible
                logger.info("Waiting for district options to load...")
                time.sleep(3)

                # Click the specific district using multiple selectors
                logger.info(f"Looking for district: {st.session_state.selected_district}")
                screenshot_manager.capture(driver, "before_searching_district")

                district_selectors = [
                    f'//a[text()="{st.session_state.selected_district}"]',
                    f'//a[contains(text(), "{st.session_state.selected_district}")]',
                    f'//*[@href and contains(text(), "{st.session_state.selected_district}")]',
                    f'//*[text()="{st.session_state.selected_district}"]',
                    f'//*[contains(text(), "{st.session_state.selected_district}")]'
                ]

                district_element = None
                for selector in district_selectors:
                    try:
                        logger.info(f"Trying district selector: {selector}")
                        district_element = wait.until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        logger.info(f"✓ Found district with: {selector}")
                        break
                    except Exception as e:
                        logger.debug(f"Selector failed: {selector}")
                        continue

                if not district_element:
                    screenshot_manager.capture_on_error(driver, "district_not_found")
                    raise Exception(f"Cannot find district: {st.session_state.selected_district}")

                logger.info(f"✓ Found district: {st.session_state.selected_district}")

                # Scroll into view and click
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", district_element)
                time.sleep(0.5)
                screenshot_manager.capture(driver, "before_clicking_district")
                driver.execute_script("arguments[0].click();", district_element)
                logger.info(f"✓ Clicked district: {st.session_state.selected_district}")
                time.sleep(2)
                screenshot_manager.capture(driver, "after_clicking_district")

                # Success!
                result = "success"
                logger.info("✅ District selection completed successfully!")

            except Exception as e:
                logger.error(f"❌ District selection failed: {e}")
                screenshot_manager.capture_on_error(driver, "district_selection_error")
                result = f"error: {e}"

        logger.info(f"🔵 District selection returned: {result}")

        # Mark as completed
        st.session_state.district_running = False
        st.session_state.completed = True
        st.session_state.result = result
        st.rerun()

    elif st.session_state.completed:
        # Show completion screen
        if hasattr(st.session_state, 'result') and st.session_state.result == "success":
            st.markdown("### ✅ Task done")
            st.markdown("")
            if st.session_state.selected_docket:
                st.markdown(f"**Selected State:** {st.session_state.selected_docket}")
            if st.session_state.selected_district:
                st.markdown(f"**Selected District:** {st.session_state.selected_district}")
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
                st.session_state.navigate_to_dockets = False
                st.session_state.dockets_nav_complete = False
                st.session_state.state_selected = False
                st.session_state.show_district_selection = False
                st.session_state.selected_district = None
                st.session_state.district_running = False
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
