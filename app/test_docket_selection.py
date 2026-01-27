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
            logger.info("Docket Number: 1:25-CV-01815")
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

            logger.info("")
            logger.info("=" * 60)
            logger.info("✓✓✓ CREATE DOCKET ALERT STEP COMPLETED! ✓✓✓")
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
