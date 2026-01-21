"""
Infrastructure Access Controls (IAC) configuration module.
Handles adding IAC values to the "IAC to be turned OFF" field.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.config.settings import settings
from src.utils.logger import get_logger
from src.utils.screenshot import ScreenshotManager
import time

logger = get_logger(__name__)


class IACConfigurator:
    """Handles Infrastructure Access Controls configuration."""

    def __init__(self):
        """Initialize the IAC configurator."""
        self.screenshot_manager = ScreenshotManager()

    def configure_iac(self, driver) -> bool:
        """
        Add IAC values to the "IAC to be turned OFF" field.

        Args:
            driver: Selenium WebDriver object

        Returns:
            True if configuration successful, False otherwise

        Raises:
            Exception: If configuration fails
        """
        try:
            logger.info("Starting Infrastructure Access Controls configuration...")

            # Find the "IAC to be turned OFF" textarea
            logger.info("Looking for 'IAC to be turned OFF' field...")

            iac_field_found = False
            iac_field = None

            # OPTIMIZED: Use XPath to find textarea with "IAC to be turned OFF" in same row
            # This is much faster than looping through all textareas
            try:
                # Try to find textarea where parent row contains "IAC to be turned OFF"
                iac_field = driver.find_element(
                    By.XPATH,
                    '//tr[contains(., "IAC to be turned OFF")]//textarea'
                )
                if iac_field:
                    logger.info("Found IAC OFF field using optimized XPath")
                    iac_field_found = True

            except Exception as e:
                logger.warning(f"Optimized XPath search failed: {e}")

                # Fallback: Loop through textareas (original method)
                try:
                    textareas = driver.find_elements(By.TAG_NAME, "textarea")
                    logger.info(f"Found {len(textareas)} textarea elements, searching...")

                    for i, textarea in enumerate(textareas):
                        try:
                            parent = textarea.find_element(By.XPATH, "./ancestor::tr")
                            if parent:
                                row_text = parent.text
                                if "IAC to be turned OFF" in row_text:
                                    logger.info(f"Found IAC OFF field (textarea #{i})")
                                    iac_field = textarea
                                    iac_field_found = True
                                    break
                        except:
                            continue

                except Exception as e2:
                    logger.warning(f"Textarea loop search failed: {e2}")

            # Fallback: Try specific XPath selectors if direct search didn't work
            if not iac_field_found:
                logger.info("Trying XPath selectors as fallback...")
                iac_off_selectors = [
                    (By.XPATH, '//td[contains(text(), "IAC to be turned OFF")]/preceding-sibling::td//textarea'),
                    (By.XPATH, '//td[text()="IAC to be turned OFF."]/preceding-sibling::td//textarea'),
                    (By.XPATH, '//td[contains(text(), "Infrastructure Access Controls")]/following::textarea[2]'),
                    (By.XPATH, '(//label[contains(text(), "Infrastructure Access Controls")]/../following::textarea)[2]')
                ]

                for by_type, selector in iac_off_selectors:
                    try:
                        iac_field = driver.find_element(by_type, selector)
                        if iac_field and iac_field.is_displayed():
                            logger.info(f"Found 'IAC to be turned OFF' field with selector: {selector}")
                            iac_field_found = True
                            break
                    except Exception as e:
                        continue

            if not iac_field_found or not iac_field:
                logger.error("Could not find 'IAC to be turned OFF' textarea field")
                self.screenshot_manager.capture_on_error(driver, "iac_field_not_found")
                raise Exception("IAC to be turned OFF field not found. Please update selectors.")

            # Clear any existing content and add the IAC values
            logger.info("Adding IAC values to 'IAC to be turned OFF' field...")

            # Format: comma-separated list
            iac_text = ", ".join(settings.IAC_VALUES)

            iac_field.clear()
            iac_field.send_keys(iac_text)

            logger.info(f"IAC values added: {iac_text}")

            # Click Save/Submit button
            logger.info("Attempting to save IAC configuration...")

            # OPTIMIZED: Put working selector first
            save_button_selectors = [
                (By.XPATH, '//input[@value="Save Changes and Sign On"]'),  # WORKING - Use this first!
                (By.XPATH, '//button[contains(text(), "Save Changes and Sign On")]'),
                (By.CSS_SELECTOR, 'input[type="submit"]'),
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.XPATH, '//input[contains(@value, "Save")]'),
                (By.XPATH, '//button[contains(text(), "Save")]')
            ]

            save_button_found = False

            for by_type, selector in save_button_selectors:
                try:
                    element = driver.find_element(by_type, selector)
                    if element and element.is_displayed() and element.is_enabled():
                        logger.info(f"Found save button with selector: {selector}")

                        # Scroll to button to ensure it's visible
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(0.5)

                        element.click()
                        logger.info("Save button clicked")
                        save_button_found = True
                        break
                except Exception as e:
                    continue

            if not save_button_found:
                logger.warning("Save button not found. Configuration may not be persisted.")
                self.screenshot_manager.capture_on_error(driver, "save_button_not_found")
                raise Exception("Save button not found. Please update selectors.")

            # Wait briefly for save to process and page redirect
            logger.info("Waiting for save confirmation and redirect...")
            time.sleep(1)

            # After clicking "Save Changes and Sign On", the page redirects to WestLaw Precision login
            logger.info("Configuration saved. Page should redirect to WestLaw Precision login...")

            logger.info("Infrastructure Access Controls configuration completed successfully")
            return True

        except Exception as e:
            logger.error(f"IAC configuration failed: {e}")
            self.screenshot_manager.capture_on_error(driver, "iac_config_error")
            raise
