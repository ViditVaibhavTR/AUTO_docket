"""
WestLaw Precision login module.
Handles login to WestLaw Precision after Cobalt Routing configuration.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.config.settings import settings
from src.utils.logger import get_logger
from src.utils.screenshot import ScreenshotManager
import time

logger = get_logger(__name__)


class WestLawLogin:
    """Handles WestLaw Precision login."""

    def __init__(self):
        """Initialize the WestLaw login handler."""
        self.screenshot_manager = ScreenshotManager()

    def login(self, driver) -> bool:
        """
        Login to WestLaw Precision using provided credentials.

        Args:
            driver: Selenium WebDriver object

        Returns:
            True if login successful, False otherwise

        Raises:
            Exception: If login fails
        """
        try:
            logger.info("Starting WestLaw Precision login...")

            # Wait for login page to load (reduced timeout)
            wait = WebDriverWait(driver, 5)

            # PRIORITIZED: Use user-provided selectors first
            username_field = None
            username_selectors = [
                (By.ID, "Username"),  # USER PRIORITIZED - Exact ID from HTML
                (By.NAME, "Username"),  # USER PRIORITIZED - Exact name from HTML
                (By.CSS_SELECTOR, 'input[type="text"]'),  # Fallback
                (By.NAME, "username"),
                (By.ID, "username"),
                (By.CSS_SELECTOR, 'input[name*="user"]')
            ]

            for by_type, selector in username_selectors:
                try:
                    username_field = wait.until(EC.presence_of_element_located((by_type, selector)))
                    logger.info(f"Found username field with selector: {by_type}={selector}")
                    break
                except:
                    continue

            if not username_field:
                logger.error("Username field not found")
                self.screenshot_manager.capture_on_error(driver, "username_field_not_found")
                raise Exception("Username field not found")

            # Enter username (no clear needed - field should be empty)
            username_field.send_keys(settings.WESTLAW_USERNAME)

            # PRIORITIZED: Use user-provided password selectors first
            password_field = None
            password_selectors = [
                (By.ID, "Password"),  # USER PRIORITIZED - Exact ID from HTML
                (By.NAME, "Password"),  # USER PRIORITIZED - Exact name from HTML
                (By.CSS_SELECTOR, 'input[type="password"]'),  # Fallback
                (By.NAME, "password"),
                (By.ID, "password")
            ]

            for by_type, selector in password_selectors:
                try:
                    password_field = driver.find_element(by_type, selector)
                    if password_field:
                        logger.info(f"Found password field with selector: {by_type}={selector}")
                        break
                except:
                    continue

            if not password_field:
                logger.error("Password field not found")
                self.screenshot_manager.capture_on_error(driver, "password_field_not_found")
                raise Exception("Password field not found")

            # Enter password (no clear needed - field should be empty)
            password_field.send_keys(settings.WESTLAW_PASSWORD)

            # PRIORITIZED: Use user-provided sign in button selectors first
            signin_button = None
            signin_selectors = [
                (By.ID, "SignIn"),  # USER PRIORITIZED - Exact ID from HTML
                (By.NAME, "SignIn"),  # USER PRIORITIZED - Exact name from HTML
                (By.XPATH, '//button[@type="submit"][@id="SignIn"]'),  # USER PRIORITIZED - Combined selector
                (By.XPATH, '//button[contains(text(), "Sign in")]'),  # Fallback
                (By.XPATH, '//button[contains(text(), "Sign In")]'),
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.XPATH, '//input[@value="Sign in"]'),
                (By.XPATH, '//input[@value="Sign In"]'),
                (By.CSS_SELECTOR, 'input[type="submit"]')
            ]

            for by_type, selector in signin_selectors:
                try:
                    signin_button = driver.find_element(by_type, selector)
                    if signin_button and signin_button.is_displayed():
                        logger.info(f"Found sign in button with selector: {selector}")
                        break
                except:
                    continue

            if not signin_button:
                logger.error("Sign in button not found")
                self.screenshot_manager.capture_on_error(driver, "signin_button_not_found")
                raise Exception("Sign in button not found")

            # Click sign in button
            signin_button.click()

            # Wait for "Select a client ID" page to load
            logger.info("Waiting for 'Select a client ID' page...")
            time.sleep(2)

            # PRIORITIZED: Use user-provided client ID field selectors first
            logger.info("Looking for client ID field...")
            client_id_field = None
            client_id_selectors = [
                (By.ID, "co_clientIDTextbox"),  # USER PRIORITIZED - Exact ID from HTML
                (By.NAME, "clientIdTextbox"),  # USER PRIORITIZED - Exact name from HTML
                (By.CSS_SELECTOR, 'input.co_clientIDTextbox'),  # USER PRIORITIZED - Exact class from HTML
                (By.CSS_SELECTOR, 'input[type="text"]'),  # Fallback
                (By.CSS_SELECTOR, 'input[name*="client"]'),
                (By.CSS_SELECTOR, 'input[placeholder*="client"]'),
                (By.XPATH, '//input[@type="text"]')
            ]

            for by_type, selector in client_id_selectors:
                try:
                    client_id_field = driver.find_element(by_type, selector)
                    if client_id_field and client_id_field.is_displayed():
                        logger.info(f"Found client ID field with selector: {by_type}={selector}")
                        break
                except:
                    continue

            if not client_id_field:
                logger.error("Client ID field not found")
                self.screenshot_manager.capture_on_error(driver, "client_id_field_not_found")
                raise Exception("Client ID field not found")

            # Enter email in client ID field
            logger.info("Entering client ID (email)...")
            from selenium.webdriver.common.keys import Keys

            # Clear any existing content
            current_value = client_id_field.get_attribute('value')
            if current_value:
                logger.info(f"Field contains '{current_value}', clearing...")
                client_id_field.send_keys(Keys.CONTROL + "a")
                time.sleep(0.1)
                client_id_field.send_keys(Keys.BACKSPACE)
                time.sleep(0.3)

            # Enter email
            logger.info("Entering email...")
            client_id_field.send_keys(settings.WESTLAW_USERNAME)
            logger.info(f"Email entered: {settings.WESTLAW_USERNAME}")

            # Wait and DON'T press escape - it might be clearing the field
            time.sleep(1.5)

            # Final check - if field is empty, enter it one more time
            final_value = client_id_field.get_attribute('value')
            if not final_value or final_value != settings.WESTLAW_USERNAME:
                logger.warning(f"Field is '{final_value}' - re-entering email...")
                # Click to focus
                client_id_field.click()
                time.sleep(0.2)
                # Clear
                client_id_field.send_keys(Keys.CONTROL + "a")
                time.sleep(0.1)
                client_id_field.send_keys(Keys.BACKSPACE)
                time.sleep(0.2)
                # Re-enter
                client_id_field.send_keys(settings.WESTLAW_USERNAME)
                logger.info("Email re-entered")
                time.sleep(1)

            # PRIORITIZED: Use user-provided start session button selectors first
            logger.info("Looking for 'Start new session' button...")
            start_session_button = None
            start_session_selectors = [
                (By.ID, "co_clientIDContinueButton"),  # USER PRIORITIZED - Exact ID from HTML
                (By.CSS_SELECTOR, 'input.co_primaryBtn'),  # USER PRIORITIZED - Exact class from HTML
                (By.XPATH, '//input[@type="button"][@id="co_clientIDContinueButton"]'),  # USER PRIORITIZED - Combined selector
                (By.XPATH, '//input[@value="Start new session"]'),  # USER PRIORITIZED - Exact value from HTML
                (By.XPATH, '//button[contains(text(), "Start new session")]'),  # Fallback
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.XPATH, '//button[contains(text(), "Start")]'),
                (By.XPATH, '//button[contains(., "new session")]')
            ]

            for by_type, selector in start_session_selectors:
                try:
                    start_session_button = driver.find_element(by_type, selector)
                    if start_session_button and start_session_button.is_displayed():
                        logger.info(f"Found start session button with selector: {by_type}={selector}")
                        break
                except:
                    continue

            if not start_session_button:
                logger.error("Start session button not found")
                self.screenshot_manager.capture_on_error(driver, "start_session_button_not_found")
                raise Exception("Start session button not found")

            # Click start session button - try regular click first, then JavaScript
            logger.info("Clicking 'Start new session' button...")
            try:
                start_session_button.click()
            except Exception as e:
                logger.warning(f"Regular click failed: {e}. Trying JavaScript click...")
                driver.execute_script("arguments[0].click();", start_session_button)

            # Wait for page to fully load after starting session
            logger.info("Waiting for WestLaw Precision home page to load...")
            time.sleep(5)  # Give page time to load completely before docket selection

            logger.info("WestLaw Precision login and session start completed successfully")
            return True

        except Exception as e:
            logger.error(f"WestLaw Precision login failed: {e}")
            self.screenshot_manager.capture_on_error(driver, "westlaw_login_error")
            raise
