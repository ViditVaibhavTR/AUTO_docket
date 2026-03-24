"""
Tab management utility for multi-docket automation.
Opens new browser tabs with a pre-built URL to skip navigation overhead.
"""

import time
from src.utils.logger import get_logger
from src.utils.smart_waits import SmartWaits

logger = get_logger(__name__)


class TabManager:
    """Manages browser tabs for multi-docket processing."""

    @staticmethod
    def open_tab_with_url(driver, url: str) -> str:
        """
        Open a new browser tab with the given URL and switch to it.
        Returns the window handle of the new tab.
        """
        # Escape single quotes in URL just in case
        safe_url = url.replace("'", "\\'")
        driver.execute_script(f"window.open('{safe_url}', '_blank');")
        time.sleep(0.5)
        new_handle = driver.window_handles[-1]
        driver.switch_to.window(new_handle)
        logger.info(f"Opened new tab with URL: {url[:80]}...")
        return new_handle

    @staticmethod
    def switch_to_tab(driver, handle: str):
        """Switch driver focus to the specified tab handle."""
        driver.switch_to.window(handle)
        logger.info(f"Switched to tab: {handle}")

    @staticmethod
    def close_extra_tabs(driver, main_handle: str):
        """Close all tabs except the main tab and switch back to it."""
        for handle in list(driver.window_handles):
            if handle != main_handle:
                driver.switch_to.window(handle)
                driver.close()
                logger.info(f"Closed extra tab: {handle}")
        driver.switch_to.window(main_handle)
        logger.info("Returned to main tab after closing extras")
