"""
Gateway configuration module for setting Gateway Live External to True.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from src.utils.logger import get_logger
from src.utils.screenshot import ScreenshotManager

logger = get_logger(__name__)


class GatewayConfigurator:
    """Handles Gateway Live External configuration."""

    def __init__(self):
        """Initialize the gateway configurator."""
        self.screenshot_manager = ScreenshotManager()

    def configure_gateway(self, driver) -> bool:
        """
        Set Gateway Live External to True.

        Args:
            driver: Selenium WebDriver object

        Returns:
            True if configuration successful, False otherwise

        Raises:
            Exception: If configuration fails
        """
        try:
            logger.info("Starting Gateway Live External configuration...")

            # Selectors for Gateway Live External dropdown
            # Ordered by priority - fastest/most reliable first
            gateway_selectors = [
                (By.CSS_SELECTOR, 'select[name*="gateway"]'),  # WORKING - Use this first!
                (By.CSS_SELECTOR, 'select[name*="Gateway"]'),
                (By.NAME, 'GatewayLive'),
                (By.NAME, 'gatewayLive'),
                (By.XPATH, '//td[contains(text(), "Gateway Live")]/following-sibling::td//select'),
                (By.XPATH, '//label[contains(text(), "Gateway Live")]/following-sibling::select')
            ]

            gateway_found = False

            # Try each selector to find the Gateway Live External element
            for by_type, selector in gateway_selectors:
                try:
                    element = driver.find_element(by_type, selector)
                    if element:
                        logger.info(f"Found Gateway Live External element with selector: {selector}")

                        # Check if it's a checkbox
                        element_type = element.get_attribute("type")
                        tag_name = element.tag_name.lower()

                        if element_type == "checkbox":
                            # Check the checkbox if not already checked
                            is_checked = element.is_selected()
                            if not is_checked:
                                element.click()
                                logger.info("Gateway Live External checkbox checked")
                            else:
                                logger.info("Gateway Live External checkbox already checked")

                        elif tag_name == "select":
                            # Select "true" or "True" option for dropdown
                            select = Select(element)
                            try:
                                select.select_by_value("true")
                            except:
                                try:
                                    select.select_by_visible_text("True")
                                except:
                                    select.select_by_visible_text("true")
                            logger.info("Gateway Live External set to True (dropdown)")

                        else:
                            # For text input, set value to "true"
                            element.clear()
                            element.send_keys("true")
                            logger.info("Gateway Live External set to True (input)")

                        gateway_found = True
                        break

                except Exception as e:
                    # Continue trying other selectors
                    continue

            if not gateway_found:
                logger.warning("Gateway Live External element not found with any known selector")
                logger.warning("Please inspect the page and update selectors in gateway_config.py")
                self.screenshot_manager.capture_on_error(driver, "gateway_element_not_found")
                raise Exception("Gateway Live External element not found. Please update selectors.")

            logger.info("Gateway Live External configuration completed successfully")
            return True

        except Exception as e:
            logger.error(f"Gateway configuration failed: {e}")
            self.screenshot_manager.capture_on_error(driver, "gateway_config_error")
            raise
