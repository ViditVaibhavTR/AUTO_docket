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


def create_docket_alert(driver):
    """
    Create Docket Alert: ONLY click notification icon and select Create Docket Alert.
    This is a separate standalone process that does NOT include form filling.

    Args:
        driver: Selenium WebDriver object

    Returns:
        "success" or "error: message"
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from src.utils.screenshot import ScreenshotManager

    screenshot_manager = ScreenshotManager()
    wait = WebDriverWait(driver, 10)

    try:
        logger.info("=" * 60)
        logger.info("CREATE DOCKET ALERT - Starting...")
        logger.info("=" * 60)

        # Wait for search results page to load
        logger.info("Waiting for search results page to load...")
        time.sleep(3)
        screenshot_manager.capture(driver, "create_alert_search_results")

        # Step 1: Find and click "Create Alert menu" button
        logger.info("Step 1: Looking for 'Create Alert menu' button...")
        notification_selectors = [
            (By.ID, 'co_search_alertMenuLink'),  # Direct ID - fastest
            (By.XPATH, '//button[@id="co_search_alertMenuLink"]'),
            (By.XPATH, '//button[@aria-label="Create Alert menu"]'),
        ]

        notification_icon = None
        for by, selector in notification_selectors:
            try:
                logger.info(f"Trying selector: {by}={selector}")
                notification_icon = wait.until(
                    EC.element_to_be_clickable((by, selector))
                )
                logger.info(f"✓ Found 'Create Alert menu' button with: {by}={selector}")
                break
            except Exception as e:
                logger.debug(f"Selector failed: {selector}")
                continue

        if not notification_icon:
            screenshot_manager.capture_on_error(driver, "create_alert_menu_not_found")
            raise Exception("Cannot find 'Create Alert menu' button")

        logger.info(f"✓ Found 'Create Alert menu' button")
        screenshot_manager.capture(driver, "before_clicking_create_alert_menu")

        # Click "Create Alert menu" button
        logger.info("Clicking 'Create Alert menu' button...")
        try:
            notification_icon.click()
            logger.info("✓ Clicked 'Create Alert menu' button")
        except:
            driver.execute_script("arguments[0].click();", notification_icon)
            logger.info("✓ Clicked 'Create Alert menu' button (JavaScript)")

        time.sleep(2)
        screenshot_manager.capture(driver, "after_clicking_create_alert_menu")

        # Step 2: Find and click "Create Docket Alert" option
        logger.info("Step 2: Looking for 'Create Docket Alert' option...")
        create_alert_selectors = [
            (By.XPATH, '//a[contains(text(), "Create Docket Alert")]'),  # WORKING - PRIORITIZED - Link element
            (By.XPATH, '//button[contains(text(), "Create Docket Alert")]'),  # Fallback - button element
            (By.XPATH, '//*[contains(text(), "Create Docket Alert")]'),  # Fallback - any element
        ]

        create_alert_button = None
        for by, selector in create_alert_selectors:
            try:
                logger.info(f"Trying selector: {by}={selector}")
                create_alert_button = wait.until(
                    EC.element_to_be_clickable((by, selector))
                )
                logger.info(f"✓ Found 'Create Docket Alert' with: {by}={selector}")
                break
            except Exception as e:
                logger.debug(f"Selector failed: {selector}")
                continue

        if not create_alert_button:
            screenshot_manager.capture_on_error(driver, "create_docket_alert_not_found")
            raise Exception("Cannot find 'Create Docket Alert' option")

        logger.info(f"✓ Found 'Create Docket Alert' option")
        screenshot_manager.capture(driver, "before_clicking_create_alert")

        # Click "Create Docket Alert"
        logger.info("Clicking 'Create Docket Alert'...")
        try:
            create_alert_button.click()
            logger.info("✓ Clicked 'Create Docket Alert'")
        except:
            driver.execute_script("arguments[0].click();", create_alert_button)
            logger.info("✓ Clicked 'Create Docket Alert' (JavaScript)")

        time.sleep(3)
        screenshot_manager.capture(driver, "after_clicking_create_alert")

        logger.info("")
        logger.info("=" * 60)
        logger.info("✓✓✓ CREATE DOCKET ALERT CLICKED! ✓✓✓")
        logger.info("Alert form should now be open")
        logger.info("=" * 60)

        return "success"

    except Exception as e:
        logger.error(f"❌ Create Docket Alert failed: {e}")
        screenshot_manager.capture_on_error(driver, "create_alert_error")
        return f"error: {e}"


def complete_alert_setup(driver, alert_name, alert_description, user_email, frequency, alert_times):
    """
    Complete Alert Setup: Fill all alert details and complete the entire flow.
    This includes: name, description, content selection, filings, email, delivery, frequency, times, and save.

    Args:
        driver: Selenium WebDriver object
        alert_name: Name for the alert
        alert_description: Description for the alert
        user_email: Email address for alert delivery
        frequency: Frequency of alerts (daily, weekdays, weekly, biweekly, monthly)
        alert_times: List of alert times to enable (e.g., ['5am', '12pm', '3pm', '5pm'])

    Returns:
        "success" or "error: message"
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from src.utils.screenshot import ScreenshotManager

    screenshot_manager = ScreenshotManager()
    wait = WebDriverWait(driver, 10)

    try:
        logger.info("=" * 60)
        logger.info("COMPLETE ALERT SETUP - Starting...")
        logger.info(f"Alert Name: {alert_name}")
        logger.info(f"Description: {alert_description}")
        logger.info(f"Email: {user_email}")
        logger.info("=" * 60)

        # Wait for alert form to load
        logger.info("Waiting for alert form to load...")
        time.sleep(2)
        screenshot_manager.capture(driver, "alert_form_loaded")

        # Step 1: Fill "Name of alert" field
        logger.info("Step 1: Filling 'Name of alert' field...")
        name_input = wait.until(
            EC.presence_of_element_located((By.ID, "optionsAlertName"))
        )
        logger.info(f"✓ Found 'Name of alert' field")
        name_input.clear()
        name_input.send_keys(alert_name)
        logger.info(f"✓ Entered alert name: {alert_name}")
        time.sleep(0.5)

        # Step 2: Fill "Description" field
        logger.info("Step 2: Filling 'Description' field...")
        description_input = wait.until(
            EC.presence_of_element_located((By.ID, "optionsAlertDescription"))
        )
        logger.info(f"✓ Found 'Description' field")
        description_input.clear()
        description_input.send_keys(alert_description)
        logger.info(f"✓ Entered description: {alert_description}")
        time.sleep(0.5)

        screenshot_manager.capture(driver, "after_filling_alert_details")

        # Step 3: Click Continue (Basics)
        logger.info("Step 3: Clicking Continue (Basics)...")
        continue_button = wait.until(
            EC.element_to_be_clickable((By.ID, "co_button_continue_Basics"))
        )
        logger.info(f"✓ Found 'Continue' button")
        try:
            continue_button.click()
            logger.info("✓ Clicked 'Continue' button")
        except:
            driver.execute_script("arguments[0].click();", continue_button)
            logger.info("✓ Clicked 'Continue' button (JavaScript)")

        time.sleep(3)
        screenshot_manager.capture(driver, "after_clicking_continue_basics")

        # Step 4: Click "All Content" tab
        logger.info("Step 4: Clicking 'All Content' tab...")
        time.sleep(2)
        all_content_tab = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//button[@role="tab"][@aria-controls="All_Content"]'))
        )
        logger.info(f"✓ Found 'All Content' tab")
        try:
            all_content_tab.click()
            logger.info("✓ Clicked 'All Content' tab")
        except:
            driver.execute_script("arguments[0].click();", all_content_tab)
            logger.info("✓ Clicked 'All Content' tab (JavaScript)")

        time.sleep(1)
        screenshot_manager.capture(driver, "after_clicking_all_content")

        # Step 5: Click Continue (Select Content)
        logger.info("Step 5: Clicking Continue (Select Content)...")
        continue_content_button = wait.until(
            EC.element_to_be_clickable((By.ID, "co_button_continue_Content"))
        )
        logger.info(f"✓ Found 'Continue' button (Select Content)")
        try:
            continue_content_button.click()
            logger.info("✓ Clicked 'Continue' button")
        except:
            driver.execute_script("arguments[0].click();", continue_content_button)
            logger.info("✓ Clicked 'Continue' button (JavaScript)")

        time.sleep(3)
        screenshot_manager.capture(driver, "after_clicking_continue_content")

        # Step 6: Click "Alert me to all new filings" radio button
        logger.info("Step 6: Clicking 'Alert me to all new filings' radio...")
        time.sleep(2)
        new_filings_radio = wait.until(
            EC.element_to_be_clickable((By.ID, "co_search_alertMeToNewFilings"))
        )
        logger.info(f"✓ Found 'Alert me to all new filings' radio button")
        try:
            new_filings_radio.click()
            logger.info("✓ Clicked radio button")
        except:
            driver.execute_script("arguments[0].click();", new_filings_radio)
            logger.info("✓ Clicked radio button (JavaScript)")

        time.sleep(1)
        screenshot_manager.capture(driver, "after_clicking_new_filings_radio")

        # Step 7: Click Continue (Enter Search Terms)
        logger.info("Step 7: Clicking Continue (Enter Search Terms)...")
        continue_search_button = wait.until(
            EC.element_to_be_clickable((By.ID, "co_button_continue_Search"))
        )
        logger.info(f"✓ Found 'Continue' button (Enter Search Terms)")
        try:
            continue_search_button.click()
            logger.info("✓ Clicked 'Continue' button")
        except:
            driver.execute_script("arguments[0].click();", continue_search_button)
            logger.info("✓ Clicked 'Continue' button (JavaScript)")

        time.sleep(3)
        screenshot_manager.capture(driver, "after_clicking_continue_search")

        # Step 8: Fill email address
        logger.info("Step 8: Filling email address...")
        time.sleep(2)

        # Click email container to activate input
        logger.info("Clicking email container to activate input...")
        email_container = wait.until(
            EC.element_to_be_clickable((By.ID, "coid_contacts_addedContactsInput_co_collaboratorWidget"))
        )
        logger.info(f"✓ Found email container")
        email_container.click()
        logger.info("✓ Clicked email container")
        time.sleep(1)

        # Fill email input
        email_input = wait.until(
            EC.element_to_be_clickable((By.ID, "coid_contacts_autoSuggest_input"))
        )
        logger.info(f"✓ Found email input field")
        email_input.clear()
        email_input.send_keys(user_email)
        logger.info(f"✓ Entered email: {user_email}")
        time.sleep(1)

        # Press Enter to confirm
        email_input.send_keys(Keys.ENTER)
        logger.info("✓ Pressed ENTER to confirm email")
        time.sleep(2)

        screenshot_manager.capture(driver, "after_filling_email")

        # Step 9: Click Continue (Customize delivery)
        logger.info("Step 9: Clicking Continue (Customize delivery)...")
        continue_delivery_button = wait.until(
            EC.element_to_be_clickable((By.ID, "co_button_continue_Delivery"))
        )
        logger.info(f"✓ Found 'Continue' button (Customize delivery)")
        try:
            continue_delivery_button.click()
            logger.info("✓ Clicked 'Continue' button")
        except:
            driver.execute_script("arguments[0].click();", continue_delivery_button)
            logger.info("✓ Clicked 'Continue' button (JavaScript)")

        time.sleep(3)
        screenshot_manager.capture(driver, "after_clicking_continue_delivery")

        # Step 10: Select frequency
        logger.info("Step 10: Selecting frequency...")
        time.sleep(2)

        from selenium.webdriver.support.ui import Select
        frequency_dropdown = wait.until(
            EC.presence_of_element_located((By.ID, "frequencySelect"))
        )
        logger.info(f"✓ Found frequency dropdown")

        select = Select(frequency_dropdown)
        select.select_by_value(frequency)
        logger.info(f"✓ Selected frequency: {frequency}")
        time.sleep(1)

        screenshot_manager.capture(driver, "after_selecting_frequency")

        # Step 11: Check alert times
        logger.info("Step 11: Checking alert times...")

        # Mapping of time labels to checkbox IDs
        time_checkbox_ids = {
            '5am': 'amExecutionTime5',
            '12pm': 'pmExecutionTime12',
            '3pm': 'pmExecutionTime3',
            '5pm': 'pmExecutionTime5'
        }

        for time_label in alert_times:
            if time_label in time_checkbox_ids:
                checkbox_id = time_checkbox_ids[time_label]
                try:
                    checkbox = wait.until(
                        EC.presence_of_element_located((By.ID, checkbox_id))
                    )

                    # Check if already checked
                    is_checked = checkbox.is_selected()
                    if not is_checked:
                        checkbox.click()
                        logger.info(f"✓ Checked {time_label} checkbox")
                    else:
                        logger.info(f"✓ {time_label} checkbox already checked")

                    time.sleep(0.3)
                except Exception as e:
                    logger.warning(f"Could not check {time_label} checkbox: {e}")

        screenshot_manager.capture(driver, "after_checking_times")

        # Step 12: Click "Save alert" button
        logger.info("Step 12: Clicking 'Save alert' button...")
        time.sleep(1)

        save_alert_button = wait.until(
            EC.element_to_be_clickable((By.ID, "co_button_saveAlert"))
        )
        logger.info(f"✓ Found 'Save alert' button")

        screenshot_manager.capture(driver, "before_clicking_save_alert")

        try:
            save_alert_button.click()
            logger.info("✓ Clicked 'Save alert' button")
        except:
            driver.execute_script("arguments[0].click();", save_alert_button)
            logger.info("✓ Clicked 'Save alert' button (JavaScript)")

        time.sleep(3)
        screenshot_manager.capture(driver, "after_clicking_save_alert")

        logger.info("")
        logger.info("=" * 60)
        logger.info("✓✓✓ COMPLETE ALERT SETUP FINISHED! ✓✓✓")
        logger.info(f"Alert Name: {alert_name}")
        logger.info(f"Description: {alert_description}")
        logger.info(f"Email: {user_email}")
        logger.info(f"Frequency: {frequency}")
        logger.info(f"Alert Times: {', '.join(alert_times)}")
        logger.info("=" * 60)

        return "success"

    except Exception as e:
        logger.error(f"❌ Complete Alert Setup failed: {e}")
        screenshot_manager.capture_on_error(driver, "complete_alert_setup_error")
        return f"error: {e}"


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
    # Phase 4: Docket number input
    if 'show_docket_number_input' not in st.session_state:
        st.session_state.show_docket_number_input = False
    if 'docket_number' not in st.session_state:
        st.session_state.docket_number = None
    if 'docket_search_running' not in st.session_state:
        st.session_state.docket_search_running = False
    # Create Docket Alert (separate process)
    if 'create_alert_running' not in st.session_state:
        st.session_state.create_alert_running = False
    if 'alert_created' not in st.session_state:
        st.session_state.alert_created = False
    # Complete Alert Setup (form filling + all steps)
    if 'show_alert_form' not in st.session_state:
        st.session_state.show_alert_form = False
    if 'alert_name_input' not in st.session_state:
        st.session_state.alert_name_input = ""
    if 'alert_description_input' not in st.session_state:
        st.session_state.alert_description_input = ""
    if 'alert_frequency' not in st.session_state:
        st.session_state.alert_frequency = "daily"
    if 'alert_times' not in st.session_state:
        st.session_state.alert_times = ["5am"]
    if 'alert_email' not in st.session_state:
        st.session_state.alert_email = ""
    if 'complete_alert_running' not in st.session_state:
        st.session_state.complete_alert_running = False
    if 'complete_alert_done' not in st.session_state:
        st.session_state.complete_alert_done = False

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

    elif st.session_state.login_completed and not st.session_state.show_docket_categories and not st.session_state.docket_running and not st.session_state.completed and not st.session_state.get('navigate_to_dockets', False) and not st.session_state.get('show_district_selection', False) and not st.session_state.get('district_running', False) and not st.session_state.get('show_docket_number_input', False) and not st.session_state.get('docket_search_running', False):
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

                # PRIORITIZED: Use user-provided Content Types tab selectors first
                logger.info("Looking for 'Content types' tab...")
                content_types_selectors = [
                    (By.ID, "tab3"),  # USER PRIORITIZED - Exact ID from HTML
                    (By.XPATH, '//li[@id="tab3"][@role="tab"]'),  # USER PRIORITIZED - Combined selector
                    (By.CSS_SELECTOR, 'li.Tab[role="tab"]#tab3'),  # USER PRIORITIZED - Class + role + ID
                    (By.XPATH, '//*[@id="tab3"]'),  # Fallback
                    (By.XPATH, '//li[contains(text(), "Content types")]'),
                    (By.XPATH, '//li[@role="tab"][contains(text(), "Content types")]')
                ]

                content_types_element = None
                for by, selector in content_types_selectors:
                    try:
                        logger.info(f"Trying selector: {by}={selector}")
                        content_types_element = wait.until(EC.presence_of_element_located((by, selector)))
                        logger.info(f"✓ Found Content Types with: {by}={selector}")
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

                # Click Dockets option - Text-based method
                logger.info("Looking for 'Dockets' option...")
                docket_selectors = [
                    (By.XPATH, '//span[contains(text(), "Dockets")]'),  # WORKING - PRIORITIZED - Use this first!
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

                # PRIORITIZED: Use user-provided state link selectors with exact href
                logger.info(f"Looking for state: {st.session_state.selected_docket}")
                screenshot_manager.capture(driver, "before_searching_state")

                # Map state names to their exact href paths (USER PRIORITIZED)
                state_href_map = {
                    "California": "/Browse/Home/Dockets/CaliforniaStateFederalDockets",
                    "New York": "/Browse/Home/Dockets/NewYorkStateFederalDockets",
                    "Texas": "/Browse/Home/Dockets/TexasStateFederalDockets"
                }

                state_href = state_href_map.get(st.session_state.selected_docket, "")

                state_selectors = []
                if state_href:
                    # USER PRIORITIZED selectors with exact href
                    state_selectors.extend([
                        (By.XPATH, f'//a[contains(@href, "{state_href}")]'),
                        (By.CSS_SELECTOR, f'a[href*="{state_href}"]'),
                    ])

                # Add fallback selectors
                state_selectors.extend([
                    (By.XPATH, f'//a[text()="{st.session_state.selected_docket}"]'),
                    (By.XPATH, f'//a[contains(text(), "{st.session_state.selected_docket}")]'),
                    (By.XPATH, f'//*[@href and contains(text(), "{st.session_state.selected_docket}")]'),
                    (By.XPATH, f'//*[text()="{st.session_state.selected_docket}"]'),
                    (By.XPATH, f'//*[contains(text(), "{st.session_state.selected_docket}")]')
                ])

                state_element = None
                for by_type, selector in state_selectors:
                    try:
                        logger.info(f"Trying state selector: {by_type}={selector}")
                        state_element = wait.until(
                            EC.element_to_be_clickable((by_type, selector))
                        )
                        logger.info(f"✓ Found state with: {by_type}={selector}")
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

        # Show 4 district options - CORRECTED ORDER
        districts = ["Central District", "Eastern District", "Northern District", "Southern District"]

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

                # PRIORITIZED: Use user-provided district link selectors with exact href
                logger.info(f"Looking for district: {st.session_state.selected_district}")
                screenshot_manager.capture(driver, "before_searching_district")

                # Map district names to their exact href paths (USER PRIORITIZED)
                district_href_map = {
                    "Central District": "CaliforniaFederalDistrictCourtDocketsCentralDistrict",
                    "Eastern District": "CaliforniaFederalDistrictCourtDocketsEasternDistrict",
                    "Northern District": "CaliforniaFederalDistrictCourtDocketsNorthernDistrict",
                    "Southern District": "CaliforniaFederalDistrictCourtDocketsSouthernDistrict"
                }

                district_href = district_href_map.get(st.session_state.selected_district, "")

                district_selectors = []
                if district_href:
                    # USER PRIORITIZED selectors with exact href
                    district_selectors.extend([
                        (By.XPATH, f'//a[contains(@href, "{district_href}")]'),
                        (By.CSS_SELECTOR, f'a[href*="{district_href}"]'),
                    ])

                # Add fallback selectors
                district_selectors.extend([
                    (By.XPATH, f'//a[text()="{st.session_state.selected_district}"]'),
                    (By.XPATH, f'//a[contains(text(), "{st.session_state.selected_district}")]'),
                    (By.XPATH, f'//*[@href and contains(text(), "{st.session_state.selected_district}")]'),
                    (By.XPATH, f'//*[text()="{st.session_state.selected_district}"]'),
                    (By.XPATH, f'//*[contains(text(), "{st.session_state.selected_district}")]')
                ])

                district_element = None
                for by_type, selector in district_selectors:
                    try:
                        logger.info(f"Trying district selector: {by_type}={selector}")
                        district_element = wait.until(
                            EC.element_to_be_clickable((by_type, selector))
                        )
                        logger.info(f"✓ Found district with: {by_type}={selector}")
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

        # Mark Phase 3 complete and show Phase 4 (docket number input)
        st.session_state.district_running = False
        st.session_state.show_docket_number_input = True  # NEW: Show Phase 4 UI
        st.rerun()

    elif st.session_state.show_docket_number_input and not st.session_state.docket_search_running and not st.session_state.completed:
        # Phase 4 UI: Docket number input
        st.markdown(f"### 🔍 Enter Docket Number")
        st.markdown("")
        st.markdown(f"**State:** {st.session_state.selected_docket}")
        st.markdown(f"**District:** {st.session_state.selected_district}")
        st.markdown("")
        st.markdown("Please enter the docket number to search:")
        st.markdown("")

        # Docket number input field
        docket_number_input = st.text_input(
            "Docket Number",
            placeholder="e.g., 1:25-CV-01815",
            key="docket_number_input_field",
            help="Enter the docket number in the format: X:YY-CV-NNNNN"
        )

        st.markdown("")

        # Submit button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔍 Search Docket", key="submit_docket_number", use_container_width=True, disabled=not docket_number_input):
                logger.info(f"🔵 User submitted docket number: {docket_number_input}")
                st.session_state.docket_number = docket_number_input
                st.session_state.show_docket_number_input = False
                st.session_state.docket_search_running = True
                st.rerun()

        st.markdown("")
        st.markdown("---")

        # Back button
        if st.button("⬅️ Back", key="back_from_docket_input"):
            st.session_state.show_docket_number_input = False
            st.session_state.show_district_selection = True
            st.rerun()

    elif st.session_state.docket_search_running and not st.session_state.completed:
        # Phase 4 Execution: Search with docket number
        logger.info(f"🟢 PHASE 4: Searching docket number {st.session_state.docket_number}")
        st.markdown("### 🔄 Searching docket...")
        st.markdown("")
        st.markdown(f"**State:** {st.session_state.selected_docket}")
        st.markdown(f"**District:** {st.session_state.selected_district}")
        st.markdown(f"**Docket Number:** {st.session_state.docket_number}")
        st.markdown("")
        st.markdown("Please wait while we:")
        st.markdown(f"1. Enter docket number: {st.session_state.docket_number}")
        st.markdown(f"2. Click the search button")
        st.markdown("")

        # Execute docket number search
        logger.info(f"🟡 Executing Docket Search → {st.session_state.docket_number}")
        with st.spinner(f"Searching for docket: {st.session_state.docket_number}..."):
            try:
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from src.utils.screenshot import ScreenshotManager

                driver = st.session_state.driver
                screenshot_manager = ScreenshotManager()
                wait = WebDriverWait(driver, 5)  # Optimized timeout

                # Wait for page to be ready
                logger.info("Waiting for docket number input field...")
                time.sleep(1)

                logger.info("=" * 60)
                logger.info("FINDING DOCKET NUMBER INPUT FIELD")
                logger.info("=" * 60)
                screenshot_manager.capture(driver, "before_docket_number_input")

                # PRIORITIZED: Use user-provided docket number input selectors first
                input_selectors = [
                    (By.ID, "co_search_advancedSearch_DN"),  # USER PRIORITIZED - Exact ID from HTML
                    (By.NAME, "co_search_advancedSearch_DN"),  # USER PRIORITIZED - Exact name from HTML
                    (By.XPATH, '//label[contains(text(), "Docket Number")]/..//input'),  # Fallback
                ]

                input_element = None
                for by, selector in input_selectors:
                    try:
                        logger.info(f"  Trying: {by}={selector}")
                        input_element = wait.until(
                            EC.presence_of_element_located((by, selector))
                        )
                        logger.info(f"  ✓ FOUND with {by}={selector}")
                        break
                    except:
                        continue

                if not input_element:
                    screenshot_manager.capture_on_error(driver, "docket_input_not_found_CRITICAL")
                    raise Exception("Cannot find docket number input field")

                logger.info(f"✓ Found docket number input field: {input_element.get_attribute('id')}")

                # Enter docket number
                logger.info(f"Entering docket number: {st.session_state.docket_number}")
                input_element.clear()
                time.sleep(0.3)  # Wait after clear before typing

                # Enter docket number and verify
                input_element.send_keys(st.session_state.docket_number)
                time.sleep(0.5)  # Wait for input to register

                # Verify the value was entered correctly
                entered_value = input_element.get_attribute('value')
                logger.info(f"Value in field: '{entered_value}'")

                if entered_value != st.session_state.docket_number:
                    logger.warning(f"Value mismatch! Expected: '{st.session_state.docket_number}', Got: '{entered_value}'")
                    logger.info("Retrying with slower input...")
                    input_element.clear()
                    time.sleep(0.5)
                    # Type character by character for reliability
                    for char in st.session_state.docket_number:
                        input_element.send_keys(char)
                        time.sleep(0.05)  # Small delay between characters
                    time.sleep(0.3)
                    entered_value = input_element.get_attribute('value')
                    logger.info(f"After retry, value in field: '{entered_value}'")

                logger.info(f"✓ Entered: {entered_value}")
                time.sleep(0.5)  # Ensure text is fully entered
                screenshot_manager.capture(driver, "after_entering_docket_number")

                # Find and click search button
                logger.info("=" * 60)
                logger.info("FINDING ORANGE SEARCH BUTTON AT TOP RIGHT")
                logger.info("=" * 60)
                screenshot_manager.capture(driver, "before_searching_for_search_button")

                # Close any open modals first
                try:
                    close_buttons = driver.find_elements(By.XPATH, '//button[contains(text(), "Close") or contains(@aria-label, "Close")]')
                    for btn in close_buttons[:3]:  # Close max 3 modals
                        try:
                            btn.click()
                            time.sleep(0.5)
                        except:
                            pass
                except:
                    pass

                # PRIORITIZED: Use user-provided search button selectors first
                search_selectors = [
                    (By.ID, "searchButton"),  # USER PRIORITIZED - Exact ID from HTML
                    (By.XPATH, '//button[@id="searchButton"]'),  # USER PRIORITIZED - Combined selector
                    (By.XPATH, '//button[contains(text(), "Search Westlaw Precision")]'),  # USER PRIORITIZED - Text match
                    (By.XPATH, '//div[contains(@class, "header") or contains(@class, "nav")]//button[contains(@aria-label, "Search") and not(contains(@aria-label, "KNOS"))]'),  # Fallback
                ]

                search_button = None
                for by, selector in search_selectors:
                    try:
                        logger.info(f"Trying search button selector: {by}={selector}")
                        search_button = wait.until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        logger.info(f"✓ Found search button with: {by}={selector}")
                        break
                    except:
                        continue

                if not search_button:
                    screenshot_manager.capture_on_error(driver, "search_button_not_found_CRITICAL")
                    raise Exception("Cannot find orange search button")

                logger.info(f"✓ Found search button: {search_button.get_attribute('id')}")
                screenshot_manager.capture(driver, "before_clicking_search")

                # Click search button
                logger.info("Clicking the orange search button...")
                try:
                    search_button.click()
                    logger.info(f"✓ Clicked search button (regular click)")
                except:
                    driver.execute_script("arguments[0].click();", search_button)
                    logger.info(f"✓ Clicked search button (JavaScript click)")

                time.sleep(2)
                screenshot_manager.capture(driver, "after_clicking_search")
                logger.info("=" * 60)
                logger.info("✓ SEARCH COMPLETED")
                logger.info("=" * 60)

                # Success!
                result = "success"
                logger.info("✅ Docket search completed successfully!")

            except Exception as e:
                logger.error(f"❌ Docket search failed: {e}")
                screenshot_manager.capture_on_error(driver, "docket_search_error")
                result = f"error: {e}"

        logger.info(f"🔵 Docket search returned: {result}")

        # Mark as completed
        st.session_state.docket_search_running = False
        st.session_state.show_district_selection = False
        st.session_state.docket_running = False
        st.session_state.show_docket_categories = False
        st.session_state.completed = True
        st.session_state.result = result
        st.rerun()

    elif st.session_state.completed and not st.session_state.create_alert_running and not st.session_state.alert_created:
        # Show completion screen with Create Docket Alert button
        if hasattr(st.session_state, 'result') and st.session_state.result == "success":
            st.markdown("### ✅ Task done")
            st.markdown("")
            if st.session_state.selected_docket:
                st.markdown(f"**Selected State:** {st.session_state.selected_docket}")
            if st.session_state.selected_district:
                st.markdown(f"**Selected District:** {st.session_state.selected_district}")
            if st.session_state.docket_number:
                st.markdown(f"**Docket Number:** {st.session_state.docket_number}")
                st.markdown(f"**Search Status:** ✅ Completed")
        else:
            st.markdown("### ❌ Task failed")
            if hasattr(st.session_state, 'result'):
                st.error(st.session_state.result)

        st.markdown("")
        st.markdown("---")

        # NEW: Create Docket Alert Button (separate process)
        if hasattr(st.session_state, 'result') and st.session_state.result == "success":
            st.markdown("### 🔔 Next Step")
            st.markdown("")
            if st.button("📝 Create Docket Alert", key="create_alert_button", use_container_width=True):
                logger.info("🔵 User clicked 'Create Docket Alert' button")
                st.session_state.create_alert_running = True
                st.rerun()

        st.markdown("")
        st.markdown("---")

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
                st.session_state.create_alert_running = False
                st.session_state.alert_created = False
                if hasattr(st.session_state, 'result'):
                    delattr(st.session_state, 'result')
                st.rerun()

        with col2:
            if st.button("🚪 Exit", key="exit_button", use_container_width=True):
                st.success("👋 Goodbye!")
                st.markdown("You can close this window now.")
                st.stop()

    elif st.session_state.create_alert_running and not st.session_state.alert_created:
        # Execute Create Docket Alert process
        logger.info("🟢 CREATE DOCKET ALERT: Starting process...")
        st.markdown("### 🔄 Creating Docket Alert...")
        st.markdown("")
        st.markdown("**Status:** ⏳ Processing...")
        st.markdown("")
        st.markdown("1. Finding 'Create Alert menu' button...")
        st.markdown("2. Clicking 'Create Docket Alert' option...")

        # Execute the create alert function
        driver = st.session_state.driver
        if driver:
            result = create_docket_alert(driver)
            logger.info(f"🔵 Create Docket Alert returned: {result}")

            # Mark as completed
            st.session_state.create_alert_running = False
            st.session_state.alert_created = True
            st.session_state.alert_result = result
            st.rerun()
        else:
            logger.error("❌ No driver available for Create Docket Alert")
            st.session_state.create_alert_running = False
            st.session_state.alert_created = True
            st.session_state.alert_result = "error: No browser session available"
            st.rerun()

    elif st.session_state.alert_created and not st.session_state.complete_alert_running and not st.session_state.complete_alert_done:
        # Show Create Docket Alert completion screen WITH FORM for alert details
        if hasattr(st.session_state, 'alert_result') and st.session_state.alert_result == "success":
            st.markdown("### ✅ Create Docket Alert Clicked!")
            st.markdown("")
            st.markdown("**Status:** ✅ Successfully clicked notification icon and selected 'Create Docket Alert'")
            st.markdown("")
            st.info("📍 Alert form is now open. Fill in the details below to complete the setup.")

            # NEW: Form for alert details
            st.markdown("")
            st.markdown("---")
            st.markdown("### 📝 Fill Alert Details")
            st.markdown("")

            # Alert Name input
            alert_name = st.text_input(
                "Name of Alert *",
                value=st.session_state.alert_name_input,
                placeholder="Enter alert name",
                key="alert_name_field"
            )

            # Description input
            alert_description = st.text_area(
                "Description (Optional)",
                value=st.session_state.alert_description_input,
                placeholder="Enter description",
                key="alert_description_field",
                height=100
            )

            st.markdown("")

            # Frequency dropdown
            alert_frequency = st.selectbox(
                "Frequency *",
                options=["daily", "weekdays", "weekly", "biweekly", "monthly"],
                format_func=lambda x: {
                    "daily": "Daily",
                    "weekdays": "Weekdays (M-F)",
                    "weekly": "Weekly",
                    "biweekly": "Bi-Weekly",
                    "monthly": "Monthly"
                }[x],
                index=["daily", "weekdays", "weekly", "biweekly", "monthly"].index(st.session_state.alert_frequency),
                key="alert_frequency_field"
            )

            st.markdown("")

            # Alert times checkboxes
            st.markdown("**Alert at these times (Central Time) ***")
            st.markdown("")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                time_5am = st.checkbox("5am", value="5am" in st.session_state.alert_times, key="time_5am")
            with col2:
                time_12pm = st.checkbox("12pm", value="12pm" in st.session_state.alert_times, key="time_12pm")
            with col3:
                time_3pm = st.checkbox("3pm", value="3pm" in st.session_state.alert_times, key="time_3pm")
            with col4:
                time_5pm = st.checkbox("5pm", value="5pm" in st.session_state.alert_times, key="time_5pm")

            st.markdown("")

            # Complete Alert Setup button
            if st.button("✅ Complete Alert Setup", key="complete_alert_button", use_container_width=True):
                # Collect selected times
                selected_times = []
                if time_5am:
                    selected_times.append("5am")
                if time_12pm:
                    selected_times.append("12pm")
                if time_3pm:
                    selected_times.append("3pm")
                if time_5pm:
                    selected_times.append("5pm")

                # Validation
                if not alert_name or alert_name.strip() == "":
                    st.error("⚠️ Please enter an alert name")
                elif len(selected_times) == 0:
                    st.error("⚠️ Please select at least one alert time")
                else:
                    logger.info(f"🔵 User clicked 'Complete Alert Setup' button")
                    logger.info(f"  Alert Name: {alert_name}")
                    logger.info(f"  Description: {alert_description}")
                    logger.info(f"  Frequency: {alert_frequency}")
                    logger.info(f"  Alert Times: {selected_times}")
                    # Save inputs to session state
                    st.session_state.alert_name_input = alert_name
                    st.session_state.alert_description_input = alert_description
                    st.session_state.alert_frequency = alert_frequency
                    st.session_state.alert_times = selected_times
                    st.session_state.complete_alert_running = True
                    st.rerun()

        else:
            st.markdown("### ❌ Create Docket Alert Failed")
            if hasattr(st.session_state, 'alert_result'):
                st.error(st.session_state.alert_result)

        st.markdown("")
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Start Over", key="restart_button2", use_container_width=True):
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
                st.session_state.create_alert_running = False
                st.session_state.alert_created = False
                st.session_state.show_alert_form = False
                st.session_state.alert_name_input = ""
                st.session_state.alert_description_input = ""
                st.session_state.alert_frequency = "daily"
                st.session_state.alert_times = ["5am"]
                st.session_state.alert_email = ""
                st.session_state.complete_alert_running = False
                st.session_state.complete_alert_done = False
                if hasattr(st.session_state, 'result'):
                    delattr(st.session_state, 'result')
                if hasattr(st.session_state, 'alert_result'):
                    delattr(st.session_state, 'alert_result')
                if hasattr(st.session_state, 'complete_alert_result'):
                    delattr(st.session_state, 'complete_alert_result')
                st.rerun()

        with col2:
            if st.button("🚪 Exit", key="exit_button2", use_container_width=True):
                st.success("👋 Goodbye!")
                st.markdown("You can close this window now.")
                st.stop()

    elif st.session_state.complete_alert_running and not st.session_state.complete_alert_done:
        # Execute Complete Alert Setup process
        logger.info("🟢 COMPLETE ALERT SETUP: Starting process...")
        st.markdown("### 🔄 Completing Alert Setup...")
        st.markdown("")
        st.markdown("**Status:** ⏳ Processing...")
        st.markdown("")
        st.markdown(f"**Alert Name:** {st.session_state.alert_name_input}")
        st.markdown(f"**Description:** {st.session_state.alert_description_input}")
        st.markdown(f"**Frequency:** {st.session_state.alert_frequency}")
        st.markdown(f"**Alert Times:** {', '.join(st.session_state.alert_times)}")
        st.markdown("")
        st.markdown("**Steps:**")
        st.markdown("1. Filling alert name and description...")
        st.markdown("2. Clicking Continue (Basics)...")
        st.markdown("3. Selecting 'All Content' tab...")
        st.markdown("4. Clicking Continue (Select Content)...")
        st.markdown("5. Selecting 'Alert me to all new filings'...")
        st.markdown("6. Clicking Continue (Enter Search Terms)...")
        st.markdown("7. Filling email address...")
        st.markdown("8. Clicking Continue (Customize delivery)...")
        st.markdown("9. Selecting frequency...")
        st.markdown("10. Checking alert times...")
        st.markdown("11. Clicking 'Save alert' button...")

        # Execute the complete alert setup function
        driver = st.session_state.driver
        if driver:
            from src.config.settings import settings
            user_email = settings.WESTLAW_USERNAME

            result = complete_alert_setup(
                driver,
                st.session_state.alert_name_input,
                st.session_state.alert_description_input,
                user_email,
                st.session_state.alert_frequency,
                st.session_state.alert_times
            )
            logger.info(f"🔵 Complete Alert Setup returned: {result}")

            # Mark as completed and save email for display
            st.session_state.complete_alert_running = False
            st.session_state.complete_alert_done = True
            st.session_state.complete_alert_result = result
            st.session_state.alert_email = user_email  # Save email to session state
            st.rerun()
        else:
            logger.error("❌ No driver available for Complete Alert Setup")
            st.session_state.complete_alert_running = False
            st.session_state.complete_alert_done = True
            st.session_state.complete_alert_result = "error: No browser session available"
            st.rerun()

    elif st.session_state.complete_alert_done:
        # Show Complete Alert Setup completion screen
        if hasattr(st.session_state, 'complete_alert_result') and st.session_state.complete_alert_result == "success":
            st.markdown("### ✅ Alert Setup Complete!")
            st.markdown("")
            st.markdown("**Alert Details:**")
            st.markdown(f"- **Name:** {st.session_state.alert_name_input}")
            st.markdown(f"- **Description:** {st.session_state.alert_description_input}")
            st.markdown(f"- **Email:** {st.session_state.alert_email}")

            # Format frequency display
            frequency_display = {
                "daily": "Daily",
                "weekdays": "Weekdays (M-F)",
                "weekly": "Weekly",
                "biweekly": "Bi-Weekly",
                "monthly": "Monthly"
            }.get(st.session_state.alert_frequency, st.session_state.alert_frequency)

            st.markdown(f"- **Frequency:** {frequency_display}")
            st.markdown(f"- **Alert Times:** {', '.join(st.session_state.alert_times)}")
            st.markdown("")
            st.markdown("**Status:** ✅ All steps completed successfully!")
            st.markdown("")
            st.success("🎉 Your docket alert has been created, configured, and saved!")
        else:
            st.markdown("### ❌ Alert Setup Failed")
            if hasattr(st.session_state, 'complete_alert_result'):
                st.error(st.session_state.complete_alert_result)

        st.markdown("")
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Start Over", key="restart_button3", use_container_width=True):
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
                st.session_state.create_alert_running = False
                st.session_state.alert_created = False
                st.session_state.show_alert_form = False
                st.session_state.alert_name_input = ""
                st.session_state.alert_description_input = ""
                st.session_state.alert_frequency = "daily"
                st.session_state.alert_times = ["5am"]
                st.session_state.alert_email = ""
                st.session_state.complete_alert_running = False
                st.session_state.complete_alert_done = False
                if hasattr(st.session_state, 'result'):
                    delattr(st.session_state, 'result')
                if hasattr(st.session_state, 'alert_result'):
                    delattr(st.session_state, 'alert_result')
                if hasattr(st.session_state, 'complete_alert_result'):
                    delattr(st.session_state, 'complete_alert_result')
                st.rerun()

        with col2:
            if st.button("🚪 Exit", key="exit_button3", use_container_width=True):
                st.success("👋 Goodbye!")
                st.markdown("You can close this window now.")
                st.stop()


if __name__ == "__main__":
    main()
