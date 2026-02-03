"""
Test script to verify docket selection functionality.
This runs independently to test the docket selection step.
"""

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


def main():
    """Test docket selection after login."""
    browser_manager = None

    try:
        logger.info("=" * 60)
        logger.info("DOCKET SELECTION TEST - Starting...")
        logger.info("=" * 60)

        # Validate configuration
        settings.validate()

        # Start browser
        logger.info("Step 1: Starting browser...")
        browser_manager = BrowserManager()
        driver = browser_manager.start()

        # Navigate to routing page
        logger.info("Step 2: Navigating to routing page...")
        browser_manager.login()

        # Configure Gateway Live External
        logger.info("Step 3: Configuring Gateway...")
        try:
            gateway_config = GatewayConfigurator()
            gateway_config.configure_gateway(driver)
        except Exception as e:
            logger.warning(f"Gateway config failed (continuing anyway): {e}")

        # Configure Infrastructure Access Controls
        logger.info("Step 4: Configuring IAC...")
        iac_config = IACConfigurator()
        iac_config.configure_iac(driver)

        # Login to WestLaw Precision
        logger.info("Step 5: Logging into WestLaw Precision...")
        westlaw_login = WestLawLogin()
        westlaw_login.login(driver)

        logger.info("✓ Login completed successfully!")
        logger.info("")
        logger.info("=" * 60)
        logger.info("NOW TESTING DOCKET SELECTION...")
        logger.info("=" * 60)

        # Wait a moment for page to stabilize
        time.sleep(2)

        # Test docket selection with California -> Southern District -> Docket Number
        logger.info("Step 6: Attempting to select docket...")
        logger.info("Testing: Dockets by State -> California -> Southern District -> 1:25-CV-01815")
        docket_selector = DocketSelector()
        success = docket_selector.select_docket(
            driver,
            category="Dockets by State",
            specific_docket="California",
            district="Southern District",
            docket_number="3:26-CV-00397"
        )

        if success:
            logger.info("")
            logger.info("=" * 60)
            logger.info("✓✓✓ DOCKET SELECTION TEST PASSED! ✓✓✓")
            logger.info("Selected: Dockets by State -> California -> Southern District")
            logger.info("Docket Number: 3:26-CV-00397")
            logger.info("=" * 60)

            # NEW STEP: Click notification icon and Create Docket Alert
            logger.info("")
            logger.info("=" * 60)
            logger.info("Step 7: Creating Docket Alert...")
            logger.info("=" * 60)

            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from src.utils.screenshot import ScreenshotManager

            screenshot_manager = ScreenshotManager()
            wait = WebDriverWait(driver, 10)

            # Wait for search results page to load
            logger.info("Waiting for search results page to load...")
            time.sleep(3)
            screenshot_manager.capture(driver, "search_results_page")

            # Find and click "Create Alert menu" button
            logger.info("Looking for 'Create Alert menu' button...")

            # First, let's list ALL buttons for debugging
            logger.info("Listing ALL buttons in header/nav area:")
            try:
                header_buttons = driver.find_elements(By.XPATH, '//header//button | //nav//button | //*[@role="navigation"]//button')
                logger.info(f"Found {len(header_buttons)} total buttons")
                for i, btn in enumerate(header_buttons):  # Log ALL buttons
                    btn_class = btn.get_attribute("class") or ""
                    btn_id = btn.get_attribute("id") or ""
                    btn_aria = btn.get_attribute("aria-label") or ""
                    btn_title = btn.get_attribute("title") or ""
                    btn_text = btn.text or ""
                    btn_visible = btn.is_displayed()
                    logger.info(f"  Btn[{i}]: id='{btn_id}', aria='{btn_aria}', title='{btn_title}', visible={btn_visible}")
            except Exception as e:
                logger.warning(f"Could not list buttons: {e}")

            # Button[32] from logs: id='co_search_alertMenuLink', aria='Create Alert menu'
            notification_selectors = [
                # PRIORITY: Direct ID of Create Alert menu button (from button enumeration)
                (By.ID, 'co_search_alertMenuLink'),  # FASTEST - Direct ID
                (By.XPATH, '//button[@id="co_search_alertMenuLink"]'),
                (By.XPATH, '//button[@aria-label="Create Alert menu"]'),
                # Fallback selectors
                (By.XPATH, '//button[contains(@aria-label, "Create Alert")]'),
                (By.XPATH, '//button[contains(@aria-label, "Alert menu")]'),
                (By.XPATH, '//button[contains(@id, "alertMenuLink")]'),
            ]

            notification_icon = None
            for by, selector in notification_selectors:
                try:
                    logger.info(f"Trying notification selector: {by}={selector}")
                    notification_icon = wait.until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    logger.info(f"✓ Found notification icon with: {by}={selector}")
                    break
                except Exception as e:
                    logger.debug(f"Selector failed: {selector}")
                    continue

            if not notification_icon:
                screenshot_manager.capture_on_error(driver, "create_alert_menu_not_found")
                raise Exception("Cannot find 'Create Alert menu' button")

            logger.info(f"✓ Found 'Create Alert menu' button")
            logger.info(f"  Element tag: {notification_icon.tag_name}")
            logger.info(f"  Element ID: {notification_icon.get_attribute('id')}")
            logger.info(f"  Element class: {notification_icon.get_attribute('class')}")
            logger.info(f"  Element aria-label: {notification_icon.get_attribute('aria-label')}")
            logger.info(f"  Element title: {notification_icon.get_attribute('title')}")

            screenshot_manager.capture(driver, "before_clicking_create_alert_menu")

            # Click "Create Alert menu" button
            logger.info("Clicking 'Create Alert menu' button...")
            try:
                notification_icon.click()
                logger.info("✓ Clicked 'Create Alert menu' button (regular click)")
            except:
                driver.execute_script("arguments[0].click();", notification_icon)
                logger.info("✓ Clicked 'Create Alert menu' button (JavaScript click)")

            time.sleep(2)
            screenshot_manager.capture(driver, "after_clicking_create_alert_menu")

            # Now find and click "Create Docket Alert" option in the menu
            logger.info("Looking for 'Create Docket Alert' option in menu...")
            create_alert_selectors = [
                (By.XPATH, '//button[contains(text(), "Create Docket Alert")]'),
                (By.XPATH, '//a[contains(text(), "Create Docket Alert")]'),
                (By.XPATH, '//*[contains(text(), "Create Docket Alert")]'),
                (By.XPATH, '//button[contains(., "Create Docket Alert")]'),
                (By.XPATH, '//a[contains(., "Create Docket Alert")]'),
                (By.XPATH, '//div[contains(text(), "Create Docket Alert")]'),
                (By.XPATH, '//span[contains(text(), "Create Docket Alert")]'),
                (By.PARTIAL_LINK_TEXT, 'Create Docket Alert'),
                (By.LINK_TEXT, 'Create Docket Alert'),
            ]

            create_alert_button = None
            for by, selector in create_alert_selectors:
                try:
                    logger.info(f"Trying create alert selector: {by}={selector}")
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
                raise Exception("Cannot find 'Create Docket Alert' option in menu")

            logger.info(f"✓ Found 'Create Docket Alert' option")
            logger.info(f"  Element tag: {create_alert_button.tag_name}")
            logger.info(f"  Element text: {create_alert_button.text}")
            logger.info(f"  Element class: {create_alert_button.get_attribute('class')}")

            screenshot_manager.capture(driver, "before_clicking_create_alert")

            # Click "Create Docket Alert"
            logger.info("Clicking 'Create Docket Alert'...")
            try:
                create_alert_button.click()
                logger.info("✓ Clicked 'Create Docket Alert' (regular click)")
            except:
                driver.execute_script("arguments[0].click();", create_alert_button)
                logger.info("✓ Clicked 'Create Docket Alert' (JavaScript click)")

            time.sleep(3)
            screenshot_manager.capture(driver, "after_clicking_create_alert")

            # NEW: Fill alert details - Name and Description
            logger.info("")
            logger.info("=" * 60)
            logger.info("Step 8: Filling Alert Details...")
            logger.info("=" * 60)

            # Wait for alert form to load
            logger.info("Waiting for alert form to load...")
            time.sleep(2)
            screenshot_manager.capture(driver, "alert_form_loaded")

            # Find and fill "Name of alert" field
            logger.info("Looking for 'Name of alert' field...")
            try:
                name_input = wait.until(
                    EC.presence_of_element_located((By.ID, "optionsAlertName"))
                )
                logger.info(f"✓ Found 'Name of alert' field: id={name_input.get_attribute('id')}")

                # Enter alert name
                alert_name = "test5"
                logger.info(f"Entering alert name: {alert_name}")
                name_input.clear()
                name_input.send_keys(alert_name)
                logger.info(f"✓ Entered alert name: {alert_name}")
                time.sleep(0.5)
            except Exception as e:
                screenshot_manager.capture_on_error(driver, "alert_name_field_not_found")
                raise Exception(f"Cannot find 'Name of alert' field: {e}")

            # Find and fill "Description (Optional)" field
            logger.info("Looking for 'Description (Optional)' field...")
            try:
                description_input = wait.until(
                    EC.presence_of_element_located((By.ID, "optionsAlertDescription"))
                )
                logger.info(f"✓ Found 'Description' field: id={description_input.get_attribute('id')}")

                # Enter description
                alert_description = "NA"
                logger.info(f"Entering description: {alert_description}")
                description_input.clear()
                description_input.send_keys(alert_description)
                logger.info(f"✓ Entered description: {alert_description}")
                time.sleep(0.5)
            except Exception as e:
                screenshot_manager.capture_on_error(driver, "alert_description_field_not_found")
                raise Exception(f"Cannot find 'Description' field: {e}")

            screenshot_manager.capture(driver, "after_filling_alert_details")

            # Find and click "Continue" button
            logger.info("Looking for 'Continue' button...")
            try:
                continue_button = wait.until(
                    EC.element_to_be_clickable((By.ID, "co_button_continue_Basics"))
                )
                logger.info(f"✓ Found 'Continue' button")
                logger.info(f"  Button ID: {continue_button.get_attribute('id')}")
                logger.info(f"  Button aria-label: {continue_button.get_attribute('aria-label')}")
                logger.info(f"  Button text: {continue_button.text}")

                screenshot_manager.capture(driver, "before_clicking_continue")

                # Click Continue button
                logger.info("Clicking 'Continue' button...")
                try:
                    continue_button.click()
                    logger.info("✓ Clicked 'Continue' button (regular click)")
                except:
                    driver.execute_script("arguments[0].click();", continue_button)
                    logger.info("✓ Clicked 'Continue' button (JavaScript click)")

                time.sleep(3)
                screenshot_manager.capture(driver, "after_clicking_continue")

            except Exception as e:
                screenshot_manager.capture_on_error(driver, "continue_button_not_found")
                raise Exception(f"Cannot find 'Continue' button: {e}")

            logger.info("")
            logger.info("=" * 60)
            logger.info("✓ ALERT DETAILS FILLED & FIRST CONTINUE CLICKED! ✓")
            logger.info(f"Alert Name: {alert_name}")
            logger.info(f"Description: {alert_description}")
            logger.info("=" * 60)

            # Step 8.1: Click "All Content" tab
            logger.info("")
            logger.info("Step 8.1: Clicking 'All Content' tab...")
            time.sleep(2)
            screenshot_manager.capture(driver, "select_content_page_loaded")

            try:
                all_content_tab = wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//button[@role="tab"][@aria-controls="All_Content"]'))
                )
                logger.info(f"✓ Found 'All Content' tab")
                logger.info(f"  Tab aria-label: {all_content_tab.get_attribute('aria-label')}")

                try:
                    all_content_tab.click()
                    logger.info("✓ Clicked 'All Content' tab (regular click)")
                except:
                    driver.execute_script("arguments[0].click();", all_content_tab)
                    logger.info("✓ Clicked 'All Content' tab (JavaScript click)")

                time.sleep(1)
                screenshot_manager.capture(driver, "after_clicking_all_content")

            except Exception as e:
                screenshot_manager.capture_on_error(driver, "all_content_tab_not_found")
                raise Exception(f"Cannot find 'All Content' tab: {e}")

            # Step 8.2: Click Continue (Select Content)
            logger.info("")
            logger.info("Step 8.2: Clicking Continue (Select Content)...")
            try:
                continue_content_button = wait.until(
                    EC.element_to_be_clickable((By.ID, "co_button_continue_Content"))
                )
                logger.info(f"✓ Found 'Continue' button (Select Content)")
                logger.info(f"  Button ID: {continue_content_button.get_attribute('id')}")
                logger.info(f"  Button aria-label: {continue_content_button.get_attribute('aria-label')}")

                screenshot_manager.capture(driver, "before_clicking_continue_content")

                try:
                    continue_content_button.click()
                    logger.info("✓ Clicked 'Continue' button (regular click)")
                except:
                    driver.execute_script("arguments[0].click();", continue_content_button)
                    logger.info("✓ Clicked 'Continue' button (JavaScript click)")

                time.sleep(3)
                screenshot_manager.capture(driver, "after_clicking_continue_content")

            except Exception as e:
                screenshot_manager.capture_on_error(driver, "continue_content_button_not_found")
                raise Exception(f"Cannot find 'Continue (Select Content)' button: {e}")

            # Step 8.3: Click "Alert me to all new filings" radio button
            logger.info("")
            logger.info("Step 8.3: Clicking 'Alert me to all new filings' radio button...")
            time.sleep(2)
            screenshot_manager.capture(driver, "filings_page_loaded")

            try:
                new_filings_radio = wait.until(
                    EC.element_to_be_clickable((By.ID, "co_search_alertMeToNewFilings"))
                )
                logger.info(f"✓ Found 'Alert me to all new filings' radio button")
                logger.info(f"  Radio ID: {new_filings_radio.get_attribute('id')}")
                logger.info(f"  Radio value: {new_filings_radio.get_attribute('value')}")

                try:
                    new_filings_radio.click()
                    logger.info("✓ Clicked 'Alert me to all new filings' radio (regular click)")
                except:
                    driver.execute_script("arguments[0].click();", new_filings_radio)
                    logger.info("✓ Clicked 'Alert me to all new filings' radio (JavaScript click)")

                time.sleep(1)
                screenshot_manager.capture(driver, "after_clicking_new_filings_radio")

            except Exception as e:
                screenshot_manager.capture_on_error(driver, "new_filings_radio_not_found")
                raise Exception(f"Cannot find 'Alert me to all new filings' radio button: {e}")

            # Step 8.4: Click Continue (Enter Search Terms)
            logger.info("")
            logger.info("Step 8.4: Clicking Continue (Enter Search Terms)...")
            try:
                # Find Continue button - ID: co_button_continue_Search
                continue_after_radio = wait.until(
                    EC.element_to_be_clickable((By.ID, "co_button_continue_Search"))
                )
                logger.info(f"✓ Found 'Continue' button (Enter Search Terms)")
                logger.info(f"  Button ID: {continue_after_radio.get_attribute('id')}")
                logger.info(f"  Button aria-label: {continue_after_radio.get_attribute('aria-label')}")

                screenshot_manager.capture(driver, "before_clicking_continue_after_radio")

                try:
                    continue_after_radio.click()
                    logger.info("✓ Clicked 'Continue' button (regular click)")
                except:
                    driver.execute_script("arguments[0].click();", continue_after_radio)
                    logger.info("✓ Clicked 'Continue' button (JavaScript click)")

                time.sleep(3)
                screenshot_manager.capture(driver, "after_clicking_continue_after_radio")

            except Exception as e:
                screenshot_manager.capture_on_error(driver, "continue_after_radio_not_found")
                raise Exception(f"Cannot find 'Continue' button after radio selection: {e}")

            # Step 8.5: Fill email address
            logger.info("")
            logger.info("Step 8.5: Filling email address...")
            time.sleep(2)
            screenshot_manager.capture(driver, "delivery_page_loaded")

            try:
                # First, click on the UL container to activate the email input
                logger.info("Clicking on email container to activate input field...")
                email_container = wait.until(
                    EC.element_to_be_clickable((By.ID, "coid_contacts_addedContactsInput_co_collaboratorWidget"))
                )
                logger.info(f"✓ Found email container")
                email_container.click()
                logger.info("✓ Clicked email container")
                time.sleep(1)

                # Now find and fill the email input field
                email_input = wait.until(
                    EC.element_to_be_clickable((By.ID, "coid_contacts_autoSuggest_input"))
                )
                logger.info(f"✓ Found email input field")
                logger.info(f"  Input ID: {email_input.get_attribute('id')}")

                # Get email from settings (already imported at top of file)
                user_email = settings.WESTLAW_USERNAME
                logger.info(f"Entering email: {user_email}")

                email_input.clear()
                email_input.send_keys(user_email)
                logger.info(f"✓ Entered email: {user_email}")
                time.sleep(1)

                # Press Enter or Tab to confirm the email
                from selenium.webdriver.common.keys import Keys
                email_input.send_keys(Keys.ENTER)
                logger.info("✓ Pressed ENTER to confirm email")
                time.sleep(2)

                screenshot_manager.capture(driver, "after_filling_email")

            except Exception as e:
                screenshot_manager.capture_on_error(driver, "email_field_not_found")
                raise Exception(f"Cannot find email field: {e}")

            # Step 8.6: Click Continue (Customize delivery)
            logger.info("")
            logger.info("Step 8.6: Clicking Continue (Customize delivery)...")
            try:
                continue_delivery_button = wait.until(
                    EC.element_to_be_clickable((By.ID, "co_button_continue_Delivery"))
                )
                logger.info(f"✓ Found 'Continue' button (Customize delivery)")
                logger.info(f"  Button ID: {continue_delivery_button.get_attribute('id')}")
                logger.info(f"  Button aria-label: {continue_delivery_button.get_attribute('aria-label')}")

                screenshot_manager.capture(driver, "before_clicking_continue_delivery")

                try:
                    continue_delivery_button.click()
                    logger.info("✓ Clicked 'Continue' button (regular click)")
                except:
                    driver.execute_script("arguments[0].click();", continue_delivery_button)
                    logger.info("✓ Clicked 'Continue' button (JavaScript click)")

                time.sleep(3)
                screenshot_manager.capture(driver, "after_clicking_continue_delivery")

            except Exception as e:
                screenshot_manager.capture_on_error(driver, "continue_delivery_button_not_found")
                raise Exception(f"Cannot find 'Continue (Customize delivery)' button: {e}")

            # Step 8.7: Select frequency
            logger.info("")
            logger.info("Step 8.7: Selecting frequency...")
            time.sleep(2)
            screenshot_manager.capture(driver, "delivery_schedule_page_loaded")

            try:
                from selenium.webdriver.support.ui import Select

                frequency_dropdown = wait.until(
                    EC.presence_of_element_located((By.ID, "frequencySelect"))
                )
                logger.info(f"✓ Found frequency dropdown")

                select = Select(frequency_dropdown)
                frequency_value = "daily"  # Test with daily
                select.select_by_value(frequency_value)
                logger.info(f"✓ Selected frequency: {frequency_value}")
                time.sleep(1)

                screenshot_manager.capture(driver, "after_selecting_frequency")

            except Exception as e:
                screenshot_manager.capture_on_error(driver, "frequency_dropdown_not_found")
                raise Exception(f"Cannot find frequency dropdown: {e}")

            # Step 8.8: Check alert times
            logger.info("")
            logger.info("Step 8.8: Checking alert times...")

            time_checkbox_ids = {
                '5am': 'amExecutionTime5',
                '12pm': 'pmExecutionTime12',
                '3pm': 'pmExecutionTime3',
                '5pm': 'pmExecutionTime5'
            }

            # Test with 5am and 12pm
            test_times = ['5am', '12pm']

            for time_label in test_times:
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

            # Step 8.9: Click "Save alert" button
            logger.info("")
            logger.info("Step 8.9: Clicking 'Save alert' button...")
            time.sleep(1)

            try:
                save_alert_button = wait.until(
                    EC.element_to_be_clickable((By.ID, "co_button_saveAlert"))
                )
                logger.info(f"✓ Found 'Save alert' button")

                screenshot_manager.capture(driver, "before_clicking_save_alert")

                try:
                    save_alert_button.click()
                    logger.info("✓ Clicked 'Save alert' button (regular click)")
                except:
                    driver.execute_script("arguments[0].click();", save_alert_button)
                    logger.info("✓ Clicked 'Save alert' button (JavaScript click)")

                time.sleep(3)
                screenshot_manager.capture(driver, "after_clicking_save_alert")

            except Exception as e:
                screenshot_manager.capture_on_error(driver, "save_alert_button_not_found")
                raise Exception(f"Cannot find 'Save alert' button: {e}")

            logger.info("")
            logger.info("=" * 60)
            logger.info("✓✓✓ COMPLETE ALERT CREATION FLOW FINISHED! ✓✓✓")
            logger.info(f"Alert Name: {alert_name}")
            logger.info(f"Description: {alert_description}")
            logger.info(f"Email: {user_email}")
            logger.info(f"Frequency: {frequency_value}")
            logger.info(f"Alert Times: {', '.join(test_times)}")
            logger.info("All steps completed successfully!")
            logger.info("=" * 60)

        else:
            logger.error("Docket selection returned False")

        # Keep browser open for verification
        logger.info("")
        logger.info("Keeping browser open for 10 seconds for manual verification...")
        time.sleep(10)

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗✗✗ TEST FAILED: {e}")
        logger.error("=" * 60)

        # Keep browser open on error
        logger.info("Keeping browser open for 10 seconds to inspect error...")
        time.sleep(10)

    finally:
        # Cleanup
        if browser_manager:
            logger.info("Cleaning up browser...")
            browser_manager.cleanup()

        logger.info("Test completed.")


if __name__ == "__main__":
    main()
