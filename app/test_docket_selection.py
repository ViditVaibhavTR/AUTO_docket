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
            docket_number="1:25-CV-01815"
        )

        if success:
            logger.info("")
            logger.info("=" * 60)
            logger.info("✓✓✓ DOCKET SELECTION TEST PASSED! ✓✓✓")
            logger.info("Selected: Dockets by State -> California -> Southern District")
            logger.info("Docket Number: 1:25-CV-01815")
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
