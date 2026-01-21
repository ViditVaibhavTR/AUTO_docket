"""
Infrastructure Access Controls (IAC) configuration module.
Handles turning OFF IAC and adding the required IAC values.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
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
        Turn OFF Infrastructure Access Controls and add IAC values.

        Args:
            driver: Selenium WebDriver object

        Returns:
            True if configuration successful, False otherwise

        Raises:
            Exception: If configuration fails
        """
        try:
            logger.info("Starting Infrastructure Access Controls configuration...")

            # Capture screenshot before configuration
            self.screenshot_manager.capture(driver, "before_iac_config")

            # TODO: Identify actual selectors by inspecting the routing page
            # The following selectors are placeholders and need to be updated

            # Step 1: Turn OFF Infrastructure Access Controls
            logger.info("Attempting to turn OFF Infrastructure Access Controls...")

            iac_toggle_selectors = [
                (By.CSS_SELECTOR, 'input[name*="infrastructure"][name*="access"]'),
                (By.CSS_SELECTOR, 'input[id*="iac"]'),
                (By.NAME, 'iacEnabled'),
                (By.CSS_SELECTOR, 'select[name*="infrastructure"]'),
                (By.XPATH, '//label[contains(text(), "Infrastructure Access Controls")]/following-sibling::input'),
                (By.XPATH, '//label[contains(text(), "Infrastructure Access Controls")]//input')
            ]

            iac_toggle_found = False

            for by_type, selector in iac_toggle_selectors:
                try:
                    element = driver.find_element(by_type, selector)
                    if element:
                        logger.info(f"Found IAC toggle element with selector: {selector}")

                        element_type = element.get_attribute("type")
                        tag_name = element.tag_name.lower()

                        if element_type == "checkbox":
                            # Uncheck the checkbox to turn OFF
                            is_checked = element.is_selected()
                            if is_checked:
                                element.click()
                                logger.info("Infrastructure Access Controls turned OFF (unchecked)")
                            else:
                                logger.info("Infrastructure Access Controls already OFF")

                        elif tag_name == "select":
                            # Select "off" or "false" option
                            select = Select(element)
                            try:
                                select.select_by_value("off")
                            except:
                                try:
                                    select.select_by_value("false")
                                except:
                                    select.select_by_visible_text("OFF")
                            logger.info("Infrastructure Access Controls set to OFF (dropdown)")

                        else:
                            # For text input, set to "off" or "false"
                            element.clear()
                            element.send_keys("off")
                            logger.info("Infrastructure Access Controls set to OFF (input)")

                        iac_toggle_found = True
                        break

                except Exception as e:
                    continue

            if not iac_toggle_found:
                logger.warning("IAC toggle element not found. Attempting to continue with IAC value configuration...")

            # Step 2: Add IAC values
            logger.info("Adding IAC values...")

            # Possible selectors for IAC value input fields
            iac_value_selectors = [
                (By.CSS_SELECTOR, 'input[name*="iac"][name*="value"]'),
                (By.CSS_SELECTOR, 'input[id*="iac"][id*="value"]'),
                (By.CSS_SELECTOR, 'textarea[name*="iac"]'),
                (By.NAME, 'iacValues'),
                (By.CSS_SELECTOR, 'textarea[name="iacValues"]')
            ]

            iac_value_field_found = False

            for by_type, selector in iac_value_selectors:
                try:
                    element = driver.find_element(by_type, selector)
                    if element:
                        logger.info(f"Found IAC value field with selector: {selector}")

                        # Check if it's a multi-line input (textarea) or single input
                        tag_name = element.tag_name.lower()

                        if tag_name == "textarea":
                            # For textarea, join values with newlines
                            iac_text = "\n".join(settings.IAC_VALUES)
                            element.clear()
                            element.send_keys(iac_text)
                            logger.info(f"IAC values added (textarea): {settings.IAC_VALUES}")
                        else:
                            # For single input, try comma-separated
                            iac_text = ", ".join(settings.IAC_VALUES)
                            element.clear()
                            element.send_keys(iac_text)
                            logger.info(f"IAC values added (input): {settings.IAC_VALUES}")

                        iac_value_field_found = True
                        break

                except Exception as e:
                    continue

            # If single input field not found, try multiple input fields
            if not iac_value_field_found:
                logger.info("Attempting to find multiple IAC input fields...")

                # Try to find multiple input fields and fill them individually
                for i, iac_value in enumerate(settings.IAC_VALUES):
                    try:
                        # Possible patterns for multiple fields
                        field_selectors = [
                            (By.NAME, f"iacValue{i}"),
                            (By.NAME, f"iacValue[{i}]"),
                            (By.ID, f"iacValue{i}")
                        ]

                        for by_type, field_selector in field_selectors:
                            try:
                                element = driver.find_element(by_type, field_selector)
                                if element:
                                    element.clear()
                                    element.send_keys(iac_value)
                                    logger.info(f"IAC value added to field {i}: {iac_value}")
                                    iac_value_field_found = True
                                    break
                            except:
                                continue
                    except:
                        continue

            if not iac_value_field_found:
                logger.warning("IAC value input fields not found with any known selector")
                logger.warning("Please inspect the page and update selectors in iac_config.py")
                self.screenshot_manager.capture_on_error(driver, "iac_fields_not_found")
                raise Exception("IAC value fields not found. Please update selectors.")

            # Capture screenshot after configuration
            self.screenshot_manager.capture(driver, "after_iac_values_config")

            # Step 3: Click Save/Submit button
            logger.info("Attempting to save IAC configuration...")

            save_button_selectors = [
                (By.XPATH, '//button[contains(text(), "Save Changes and Sign On")]'),
                (By.XPATH, '//input[@value="Save Changes and Sign On"]'),
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.CSS_SELECTOR, 'input[type="submit"]'),
                (By.XPATH, '//button[contains(text(), "Save")]'),
                (By.XPATH, '//button[contains(text(), "Submit")]'),
                (By.XPATH, '//button[contains(text(), "Apply")]'),
                (By.NAME, 'save'),
                (By.CSS_SELECTOR, 'button[id*="save"]'),
                (By.CSS_SELECTOR, 'button[id*="submit"]')
            ]

            save_button_found = False

            for by_type, selector in save_button_selectors:
                try:
                    element = driver.find_element(by_type, selector)
                    if element:
                        # Check if button is visible and enabled
                        is_visible = element.is_displayed()
                        is_enabled = element.is_enabled()

                        if is_visible and is_enabled:
                            logger.info(f"Found save button with selector: {selector}")
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

            # Wait for save confirmation
            try:
                # Wait for possible success message or page reload
                wait = WebDriverWait(driver, 10)
                logger.info("Waiting for save confirmation...")

                # Look for success message
                success_selectors = [
                    (By.XPATH, '//*[contains(text(), "Success")]'),
                    (By.XPATH, '//*[contains(text(), "Saved")]'),
                    (By.XPATH, '//*[contains(text(), "Configuration saved")]'),
                    (By.CLASS_NAME, 'success-message'),
                    (By.CLASS_NAME, 'alert-success')
                ]

                for by_type, selector in success_selectors:
                    try:
                        element = wait.until(EC.presence_of_element_located((by_type, selector)))
                        if element:
                            logger.info("Success message detected")
                            break
                    except:
                        continue

                # Wait a moment for any animations/transitions
                time.sleep(1)

            except Exception as e:
                logger.warning(f"Could not confirm save operation: {e}")

            # Capture final screenshot
            self.screenshot_manager.capture_success(driver, "iac_config_complete")

            logger.info("Infrastructure Access Controls configuration completed successfully")
            return True

        except Exception as e:
            logger.error(f"IAC configuration failed: {e}")
            self.screenshot_manager.capture_on_error(driver, "iac_config_error")
            raise
