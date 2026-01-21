"""
Browser automation module for the Docket Alert project.
Handles browser initialization, login, and navigation using Selenium.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from src.config.settings import settings
from src.utils.logger import get_logger
from src.utils.screenshot import ScreenshotManager

logger = get_logger(__name__)


class BrowserManager:
    """Manages browser lifecycle and authentication."""

    def __init__(self):
        """Initialize the browser manager."""
        self.driver = None
        self.wait = None
        self.screenshot_manager = ScreenshotManager()

    def start(self):
        """
        Start the browser and initialize WebDriver.

        Returns:
            Selenium WebDriver object

        Raises:
            Exception: If browser initialization fails
        """
        try:
            logger.info("Starting browser...")

            # Configure Chrome options
            chrome_options = Options()

            if settings.HEADLESS:
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-gpu")

            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # Initialize Chrome driver with webdriver-manager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Set implicit wait (reduced for faster execution)
            self.driver.implicitly_wait(3)

            # Initialize explicit wait (reduced for faster execution)
            self.wait = WebDriverWait(self.driver, 10)

            logger.info("Browser started successfully")
            return self.driver

        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            self.cleanup()
            raise

    def login(self) -> bool:
        """
        Navigate to West Classic application (already authenticated via browser).

        Returns:
            True if navigation successful, False otherwise

        Raises:
            Exception: If navigation fails
        """
        if not self.driver:
            raise Exception("Browser not initialized. Call start() first.")

        try:
            logger.info(f"Navigating to routing page: {settings.WESTLAW_URL}")
            logger.info("Note: Assuming user is already authenticated in browser")

            self.driver.get(settings.WESTLAW_URL)

            # Wait for page to load
            self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")

            logger.info("Page loaded successfully (no login required - using existing session)")
            return True

        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            if self.driver:
                self.screenshot_manager.capture_on_error(self.driver, "navigation_error")
            raise

    def navigate_to_routing(self) -> bool:
        """
        Navigate to the routing page after login.

        Returns:
            True if navigation successful, False otherwise
        """
        if not self.driver:
            raise Exception("Browser not initialized. Call start() first.")

        try:
            logger.info(f"Navigating to routing page: {settings.WESTLAW_URL}")
            self.driver.get(settings.WESTLAW_URL)

            # Wait for page to load
            self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")

            # Capture screenshot of routing page
            self.screenshot_manager.capture(self.driver, "routing_page")

            logger.info("Successfully navigated to routing page")
            return True

        except Exception as e:
            logger.error(f"Failed to navigate to routing page: {e}")
            if self.driver:
                self.screenshot_manager.capture_on_error(self.driver, "navigation_error")
            raise

    def cleanup(self) -> None:
        """Clean up browser resources."""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Browser cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
