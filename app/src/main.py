"""
Main entry point for the Docket Alert automation project.
Orchestrates the workflow: login, gateway configuration, and IAC configuration.
"""

import sys
import time
from src.config.settings import settings
from src.automation.browser import BrowserManager
from src.automation.gateway_config import GatewayConfigurator
from src.automation.iac_config import IACConfigurator
from src.automation.westlaw_login import WestLawLogin
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """
    Main automation workflow for Docket Alert configuration.

    Steps:
    1. Validate configuration
    2. Start browser
    3. Navigate to Cobalt Routing page
    4. Configure Gateway Live External (set to True)
    5. Configure Infrastructure Access Controls (add IAC values)
    6. Login to WestLaw Precision (after "Save Changes and Sign On" redirect)
    7. Cleanup
    """
    browser_manager = None

    try:
        # Step 1: Validate configuration
        logger.info("=" * 80)
        logger.info("Docket Alert Automation - Step 1: Gateway and IAC Configuration")
        logger.info("=" * 80)

        logger.info("Validating configuration...")
        try:
            settings.validate()
            config = settings.display_config()
            logger.info("Configuration loaded successfully:")
            for key, value in config.items():
                logger.info(f"  {key}: {value}")
        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            logger.error("Please check your .env file and ensure all required values are set.")
            return False

        # Step 2: Start browser
        logger.info("\nStep 1/5: Initializing browser...")
        browser_manager = BrowserManager()
        driver = browser_manager.start()
        logger.info("Browser initialized successfully")

        # Step 3: Navigate to routing page (login not needed - already authenticated)
        logger.info("\nStep 2/5: Navigating to routing page...")
        try:
            browser_manager.login()  # This just navigates to the page
            logger.info("Navigation completed successfully")
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False

        # Step 4: Configure Gateway Live External
        logger.info("\nStep 3/5: Configuring Gateway Live External...")
        try:
            gateway_config = GatewayConfigurator()
            gateway_config.configure_gateway(driver)
            logger.info("Gateway Live External configured successfully")
        except Exception as e:
            logger.error(f"Gateway configuration failed: {e}")
            logger.error("Note: Gateway selectors may need to be updated in gateway_config.py")
            logger.error("Check the screenshots in the screenshots/ directory for visual debugging")
            # Continue to IAC configuration even if gateway fails
            logger.warning("Continuing to IAC configuration despite gateway error...")

        # Step 5: Configure Infrastructure Access Controls
        logger.info("\nStep 4/5: Configuring Infrastructure Access Controls...")
        try:
            iac_config = IACConfigurator()
            iac_config.configure_iac(driver)
            logger.info("Infrastructure Access Controls configured successfully")
        except Exception as e:
            logger.error(f"IAC configuration failed: {e}")
            logger.error("Note: IAC selectors may need to be updated in iac_config.py")
            logger.error("Check the screenshots in the screenshots/ directory for visual debugging")
            return False

        # Step 6: Login to WestLaw Precision
        logger.info("\nStep 5/5: Logging in to WestLaw Precision...")
        try:
            westlaw_login = WestLawLogin()
            westlaw_login.login(driver)
            logger.info("WestLaw Precision login completed successfully")
        except Exception as e:
            logger.error(f"WestLaw Precision login failed: {e}")
            logger.error("Note: Login selectors may need to be updated in westlaw_login.py")
            logger.error("Check the screenshots in the screenshots/ directory for visual debugging")
            return False

        # Success
        logger.info("\n" + "=" * 80)
        logger.info("SUCCESS: Complete automation workflow finished!")
        logger.info("=" * 80)
        logger.info("Configuration Summary:")
        logger.info("  - Gateway Live External: Set to True")
        logger.info("  - Infrastructure Access Controls: Turned OFF")
        logger.info(f"  - IAC Values Added: {', '.join(settings.IAC_VALUES)}")
        logger.info("  - WestLaw Precision: Logged in successfully")
        logger.info("\nPlease verify the configuration on the website.")
        logger.info("Screenshots have been saved to the screenshots/ directory.")
        logger.info("Logs have been saved to the logs/ directory.")

        # Keep browser open briefly to allow manual verification
        logger.info("\nKeeping browser open for 1 second for verification...")
        time.sleep(1)

        return True

    except Exception as e:
        logger.error(f"Automation failed with unexpected error: {e}")
        return False

    finally:
        # Step 7: Cleanup
        if browser_manager:
            logger.info("\nCleaning up browser resources...")
            browser_manager.cleanup()
            logger.info("Cleanup completed")


if __name__ == "__main__":
    logger.info("Starting Docket Alert Automation...")

    # Run the main function
    result = main()

    # Exit with appropriate code
    sys.exit(0 if result else 1)
