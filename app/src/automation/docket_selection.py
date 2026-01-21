"""
Docket selection module for WestLaw Precision.
Handles selecting "Dockets" from the Content Types after login.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.utils.logger import get_logger
from src.utils.screenshot import ScreenshotManager
import time

logger = get_logger(__name__)


class DocketSelector:
    """Handles docket selection in WestLaw Precision."""

    def __init__(self):
        """Initialize the docket selector."""
        self.screenshot_manager = ScreenshotManager()

    def select_docket(self, driver, category=None, specific_docket=None) -> bool:
        """
        Select "Dockets" from Content Types in WestLaw Precision,
        and optionally select a specific category and docket.

        Args:
            driver: Selenium WebDriver object
            category: Optional category name (e.g., "Dockets by State")
            specific_docket: Optional specific docket name (e.g., "California")

        Returns:
            True if selection successful, False otherwise

        Raises:
            Exception: If selection fails
        """
        try:
            logger.info("Starting docket selection...")
            if category:
                logger.info(f"Category: {category}")
            if specific_docket:
                logger.info(f"Specific docket: {specific_docket}")

            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            # Wait for page to stabilize after login
            logger.info("Waiting for page to load...")
            time.sleep(3)

            logger.info(f"Current URL: {driver.current_url}")

            # Take screenshot of the page before searching
            self.screenshot_manager.capture(driver, "before_content_types_search")
            logger.info("Screenshot saved: before_content_types_search")

            # First, click on "Content types" tab in the navigation
            logger.info("Looking for 'Content types' tab in navigation...")

            # Try to find Content types tab in navigation
            content_types_selectors = [
                '//*[@id="tab3"]',  # Direct ID from HTML
                '//li[contains(text(), "Content types")]',
                '//li[@role="tab"][contains(text(), "Content types")]',
                '//li[@class="Tab"][contains(text(), "Content types")]',
                '//*[@role="tab" and contains(text(), "Content types")]',
                '//a[contains(text(), "Content types")]',
                '//button[contains(text(), "Content types")]'
            ]

            content_types_element = None
            for selector in content_types_selectors:
                try:
                    # Use shorter wait for each attempt
                    short_wait = WebDriverWait(driver, 2)
                    logger.info(f"Trying: {selector}")
                    content_types_element = short_wait.until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    logger.info(f"✓ Found Content Types with: {selector}")

                    # Scroll into view and click
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", content_types_element)
                    time.sleep(0.5)
                    self.screenshot_manager.capture(driver, "before_clicking_content_types")
                    driver.execute_script("arguments[0].click();", content_types_element)
                    logger.info("✓ Clicked Content Types section")
                    time.sleep(2)  # Wait for dropdown/section to expand
                    self.screenshot_manager.capture(driver, "after_clicking_content_types")
                    logger.info("Screenshot saved: after_clicking_content_types")
                    break
                except Exception as e:
                    continue

            if not content_types_element:
                logger.error("FAILED: Content Types section not found with any selector")
                self.screenshot_manager.capture_on_error(driver, "content_types_not_found")
                # Save page source for debugging
                try:
                    with open("debug_page_source.html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    logger.info("Saved page source to debug_page_source.html")
                except:
                    pass
                raise Exception("Cannot find Content Types section on page")

            # Find and click "Dockets" option
            logger.info("Looking for 'Dockets' option...")

            dockets_selectors = [
                '//span[contains(text(), "Dockets")]',
                '//div[contains(text(), "Dockets")]',
                '//a[contains(text(), "Dockets")]',
                '//button[contains(text(), "Dockets")]',
                '//label[contains(text(), "Dockets")]',
                '//*[text()="Dockets"]',
                '//*[contains(text(), "Docket")]'
            ]

            dockets_element = None
            for selector in dockets_selectors:
                try:
                    short_wait = WebDriverWait(driver, 2)
                    logger.info(f"Trying: {selector}")
                    dockets_element = short_wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    logger.info(f"✓ Found Dockets with: {selector}")
                    break
                except Exception as e:
                    continue

            if not dockets_element:
                logger.error("FAILED: Dockets element not found with any selector")
                self.screenshot_manager.capture_on_error(driver, "dockets_not_found")
                # Save page source
                try:
                    with open("debug_page_after_content_types.html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    logger.info("Saved page source to debug_page_after_content_types.html")
                except:
                    pass
                raise Exception("Cannot find Dockets option after clicking Content Types")

            logger.info("Clicking Dockets...")
            driver.execute_script("arguments[0].click();", dockets_element)
            logger.info("✓ Successfully clicked Dockets")
            time.sleep(2)  # Wait for dockets panel to appear
            self.screenshot_manager.capture(driver, "after_clicking_dockets")
            logger.info("Screenshot saved: after_clicking_dockets")

            # If category and specific_docket are provided, continue with hierarchical selection
            if category and specific_docket:
                # Wait for docket options to appear
                logger.info(f"Waiting for docket categories to load...")
                time.sleep(2)

                # Define wait with longer timeout for category selection
                category_wait = WebDriverWait(driver, 10)

                # Find and click the category
                logger.info(f"Looking for category: {category}")
                try:
                    category_element = category_wait.until(
                        EC.element_to_be_clickable((By.XPATH, f'//*[contains(text(), "{category}")]'))
                    )
                    logger.info(f"✓ Found category: {category}")
                    self.screenshot_manager.capture(driver, "before_clicking_category")
                    driver.execute_script("arguments[0].click();", category_element)
                    logger.info(f"✓ Clicked on category: {category}")
                    time.sleep(2)
                    self.screenshot_manager.capture(driver, "after_clicking_category")
                except Exception as e:
                    logger.error(f"Failed to find category '{category}': {str(e)}")
                    self.screenshot_manager.capture_on_error(driver, "category_not_found")
                    raise

                # Wait for specific docket options to appear
                logger.info(f"Waiting for specific dockets to load...")
                time.sleep(1)

                # Find and click the specific docket
                logger.info(f"Looking for specific docket: {specific_docket}")
                try:
                    docket_wait = WebDriverWait(driver, 10)
                    docket_element = docket_wait.until(
                        EC.element_to_be_clickable((By.XPATH, f'//*[contains(text(), "{specific_docket}")]'))
                    )
                    logger.info(f"✓ Found specific docket: {specific_docket}")
                    self.screenshot_manager.capture(driver, "before_clicking_specific_docket")
                    driver.execute_script("arguments[0].click();", docket_element)
                    logger.info(f"✓ Clicked on specific docket: {specific_docket}")
                    time.sleep(1)
                    self.screenshot_manager.capture(driver, "after_clicking_specific_docket")
                except Exception as e:
                    logger.error(f"Failed to find specific docket '{specific_docket}': {str(e)}")
                    self.screenshot_manager.capture_on_error(driver, "specific_docket_not_found")
                    raise

            logger.info("Docket selection completed successfully")
            return True

        except Exception as e:
            logger.error(f"Docket selection failed: {e}")
            self.screenshot_manager.capture_on_error(driver, "docket_selection_error")
            raise
