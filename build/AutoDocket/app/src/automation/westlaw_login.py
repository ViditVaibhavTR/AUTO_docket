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

            # Check if field already has a valid value
            current_value = client_id_field.get_attribute('value')
            if current_value and current_value.strip():
                logger.info(f"✓ Client ID field already has value: '{current_value}'")
                logger.info("Skipping re-entry - will use prefilled value")

                # Dismiss any autocomplete dropdown
                logger.info("Dismissing autocomplete dropdown...")
                try:
                    client_id_field.send_keys(Keys.ESCAPE)
                    time.sleep(0.2)
                    driver.execute_script("""
                        if (document.activeElement) {
                            document.activeElement.blur();
                        }
                    """)
                    time.sleep(0.1)
                    logger.info("✓ Autocomplete dropdown dismissed")
                except Exception as e:
                    logger.warning(f"Could not dismiss autocomplete: {e}")

                # Skip to button click - no need to clear or re-enter

            else:
                # Field is empty - enter the email
                logger.info("Client ID field is empty, entering email...")

                # Enter email
                client_id_field.send_keys(settings.WESTLAW_USERNAME)
                logger.info(f"Email entered: {settings.WESTLAW_USERNAME}")
                time.sleep(1.5)

                # Verify entry
                final_value = client_id_field.get_attribute('value')
                if not final_value or final_value != settings.WESTLAW_USERNAME:
                    logger.warning(f"Email verification failed. Expected: {settings.WESTLAW_USERNAME}, Got: {final_value}")
                    logger.info("Attempting re-entry...")

                    # Try one more time
                    client_id_field.clear()
                    time.sleep(0.2)
                    client_id_field.send_keys(settings.WESTLAW_USERNAME)
                    time.sleep(0.5)

                    # Final check
                    final_value = client_id_field.get_attribute('value')
                    if final_value == settings.WESTLAW_USERNAME:
                        logger.info("✓ Email re-entry successful")
                    else:
                        logger.error(f"Email entry failed after retry. Got: {final_value}")
                else:
                    logger.info("✓ Email verified successfully")

                # Dismiss autocomplete dropdown
                logger.info("Dismissing autocomplete dropdown...")
                try:
                    client_id_field.send_keys(Keys.ESCAPE)
                    time.sleep(0.2)
                    driver.execute_script("""
                        if (document.activeElement) {
                            document.activeElement.blur();
                        }
                    """)
                    time.sleep(0.1)
                    logger.info("✓ Autocomplete dropdown dismissed")
                except Exception as e:
                    logger.warning(f"Could not dismiss autocomplete: {e}")

            # Continue to button click
            logger.info("Looking for 'Start new session' button...")

            # Wait a moment for page to stabilize after client ID entry
            time.sleep(1)

            start_session_button = None
            start_session_selectors = [
                (By.ID, "co_clientIDContinueButton"),  # PRIMARY
                (By.XPATH, '//input[@value="Start new session"]'),
                (By.XPATH, '//button[contains(text(), "Start new session")]'),
                (By.CSS_SELECTOR, 'input.co_primaryBtn'),
                (By.XPATH, '//input[@type="button"][@id="co_clientIDContinueButton"]'),
                (By.XPATH, '//input[@type="submit"]'),
                (By.XPATH, '//button[@type="submit"]'),
                (By.CSS_SELECTOR, 'button.co_primaryBtn'),
                (By.XPATH, '//input[contains(@value, "Start")]'),
                (By.XPATH, '//button[contains(text(), "Start")]')
            ]

            # Try to find button with each selector
            for by_type, selector in start_session_selectors:
                try:
                    logger.info(f"Trying selector: {by_type}={selector}")

                    # Find the element (without requiring it to be displayed yet)
                    element = driver.find_element(by_type, selector)

                    if element:
                        logger.info(f"✓ Found element with {by_type}={selector}")

                        # Scroll element into view to make it visible
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                        time.sleep(0.5)  # Wait for scroll

                        # Check if now displayed
                        if element.is_displayed():
                            logger.info(f"✓ Element is displayed after scroll")
                            start_session_button = element
                            break
                        else:
                            logger.warning(f"Element found but still not displayed: {by_type}={selector}")
                            # Try next selector
                            continue
                except Exception as e:
                    logger.debug(f"Selector {by_type}={selector} failed: {e}")
                    continue

            # If still not found, try without visibility check (use JavaScript)
            if not start_session_button:
                logger.warning("Button not found with visibility check - trying without display requirement...")

                for by_type, selector in start_session_selectors:
                    try:
                        element = driver.find_element(by_type, selector)
                        if element:
                            logger.info(f"Found element (no visibility check): {by_type}={selector}")
                            start_session_button = element
                            break
                    except:
                        continue

            # Final check
            if not start_session_button:
                logger.error("FAILED: Start session button not found with any selector")
                self.screenshot_manager.capture_on_error(driver, "start_session_button_not_found")

                # Save page source for debugging
                try:
                    with open("debug_login_page.html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    logger.info("Saved page source to debug_login_page.html")
                except:
                    pass

                raise Exception("Start session button not found on page")

            # Click the button
            logger.info("Clicking 'Start new session' button...")
            self.screenshot_manager.capture(driver, "before_clicking_start_session")

            try:
                # Try regular click first
                start_session_button.click()
                logger.info("✓ Clicked button using regular click")
            except Exception as e:
                logger.warning(f"Regular click failed: {e}. Trying JavaScript click...")
                try:
                    driver.execute_script("arguments[0].click();", start_session_button)
                    logger.info("✓ Clicked button using JavaScript click")
                except Exception as js_error:
                    logger.error(f"JavaScript click also failed: {js_error}")
                    self.screenshot_manager.capture_on_error(driver, "button_click_failed")
                    raise Exception(f"Failed to click Start new session button: {js_error}")

            logger.info("✓ Clicked Start new session button")

            # Wait for navigation to WestLaw Precision home page
            logger.info("Waiting for WestLaw Precision home page to load...")
            time.sleep(5)

            logger.info("WestLaw Precision login and session start completed successfully")
            return True

        except Exception as e:
            logger.error(f"WestLaw Precision login failed: {e}")
            self.screenshot_manager.capture_on_error(driver, "westlaw_login_error")
            raise
