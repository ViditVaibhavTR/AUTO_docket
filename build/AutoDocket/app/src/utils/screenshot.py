"""
Screenshot utility for the Docket Alert automation project.
Captures screenshots at key workflow steps and on errors.
"""

from pathlib import Path
from datetime import datetime


class ScreenshotManager:
    """Manages screenshot capture and storage."""

    def __init__(self):
        """Initialize the screenshot manager."""
        self.screenshot_dir = Path(__file__).parent.parent.parent / "screenshots"
        self.screenshot_dir.mkdir(exist_ok=True)

    def capture(self, driver, name: str, prefix: str = "") -> str:
        """
        Capture a screenshot with a timestamped filename.

        Args:
            driver: Selenium WebDriver object
            name: Descriptive name for the screenshot
            prefix: Optional prefix for the filename (e.g., "error", "success")

        Returns:
            Path to the saved screenshot
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix_part = f"{prefix}_" if prefix else ""
        filename = f"{prefix_part}{name}_{timestamp}.png"
        filepath = self.screenshot_dir / filename

        driver.save_screenshot(str(filepath))
        return str(filepath)

    def capture_on_error(self, driver, error_context: str) -> str:
        """
        Capture a screenshot when an error occurs.

        Args:
            driver: Selenium WebDriver object
            error_context: Description of the error context

        Returns:
            Path to the saved screenshot
        """
        return self.capture(driver, error_context, prefix="error")

    def capture_success(self, driver, step_name: str) -> str:
        """
        Capture a screenshot after a successful step.

        Args:
            driver: Selenium WebDriver object
            step_name: Name of the completed step

        Returns:
            Path to the saved screenshot
        """
        return self.capture(driver, step_name, prefix="success")
