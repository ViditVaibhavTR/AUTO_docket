"""
Infrastructure Access Controls (IAC) configuration module.
Handles turning OFF IAC and adding the required IAC values.
"""

from playwright.async_api import Page
from src.config.settings import settings
from src.utils.logger import get_logger
from src.utils.screenshot import ScreenshotManager

logger = get_logger(__name__)


class IACConfigurator:
    """Handles Infrastructure Access Controls configuration."""

    def __init__(self):
        """Initialize the IAC configurator."""
        self.screenshot_manager = ScreenshotManager()

    async def configure_iac(self, page: Page) -> bool:
        """
        Turn OFF Infrastructure Access Controls and add IAC values.

        Args:
            page: Playwright page object

        Returns:
            True if configuration successful, False otherwise

        Raises:
            Exception: If configuration fails
        """
        try:
            logger.info("Starting Infrastructure Access Controls configuration...")

            # Capture screenshot before configuration
            await self.screenshot_manager.capture(page, "before_iac_config")

            # TODO: Identify actual selectors by inspecting the routing page
            # The following selectors are placeholders and need to be updated

            # Step 1: Turn OFF Infrastructure Access Controls
            logger.info("Attempting to turn OFF Infrastructure Access Controls...")

            iac_toggle_selectors = [
                'input[name*="infrastructure"][name*="access"]',
                'input[id*="iac"]',
                'input[name="iacEnabled"]',
                'select[name*="infrastructure"]',
                'label:has-text("Infrastructure Access Controls") + input',
                'label:has-text("Infrastructure Access Controls") input'
            ]

            iac_toggle_found = False

            for selector in iac_toggle_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        logger.info(f"Found IAC toggle element with selector: {selector}")

                        element_type = await element.get_attribute("type")

                        if element_type == "checkbox":
                            # Uncheck the checkbox to turn OFF
                            is_checked = await element.is_checked()
                            if is_checked:
                                await element.uncheck()
                                logger.info("Infrastructure Access Controls turned OFF (unchecked)")
                            else:
                                logger.info("Infrastructure Access Controls already OFF")

                        elif element_type == "select" or await element.evaluate("el => el.tagName") == "SELECT":
                            # Select "off" or "false" option
                            try:
                                await page.select_option(selector, value="off")
                            except:
                                await page.select_option(selector, value="false")
                            logger.info("Infrastructure Access Controls set to OFF (dropdown)")

                        else:
                            # For text input, set to "off" or "false"
                            await element.fill("off")
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
                'input[name*="iac"][name*="value"]',
                'input[id*="iac"][id*="value"]',
                'textarea[name*="iac"]',
                'input[name="iacValues"]',
                'textarea[name="iacValues"]'
            ]

            iac_value_field_found = False

            for selector in iac_value_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        logger.info(f"Found IAC value field with selector: {selector}")

                        # Check if it's a multi-line input (textarea) or single input
                        tag_name = await element.evaluate("el => el.tagName")

                        if tag_name.lower() == "textarea":
                            # For textarea, join values with newlines
                            iac_text = "\n".join(settings.IAC_VALUES)
                            await element.fill(iac_text)
                            logger.info(f"IAC values added (textarea): {settings.IAC_VALUES}")
                        else:
                            # For single input, try comma-separated
                            iac_text = ", ".join(settings.IAC_VALUES)
                            await element.fill(iac_text)
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
                        field_selector = f'input[name="iacValue{i}"], input[name="iacValue[{i}]"], input[id="iacValue{i}"]'
                        element = await page.query_selector(field_selector)

                        if element:
                            await element.fill(iac_value)
                            logger.info(f"IAC value added to field {i}: {iac_value}")
                            iac_value_field_found = True
                    except:
                        continue

            if not iac_value_field_found:
                logger.warning("IAC value input fields not found with any known selector")
                logger.warning("Please inspect the page and update selectors in iac_config.py")
                await self.screenshot_manager.capture_on_error(page, "iac_fields_not_found")
                raise Exception("IAC value fields not found. Please update selectors.")

            # Capture screenshot after configuration
            await self.screenshot_manager.capture(page, "after_iac_values_config")

            # Step 3: Click Save/Submit button
            logger.info("Attempting to save IAC configuration...")

            save_button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Save")',
                'button:has-text("Submit")',
                'button:has-text("Apply")',
                'button[name="save"]',
                'button[id*="save"]',
                'button[id*="submit"]'
            ]

            save_button_found = False

            for selector in save_button_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        # Check if button is visible and enabled
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()

                        if is_visible and is_enabled:
                            logger.info(f"Found save button with selector: {selector}")
                            await element.click()
                            logger.info("Save button clicked")
                            save_button_found = True
                            break
                except Exception as e:
                    continue

            if not save_button_found:
                logger.warning("Save button not found. Configuration may not be persisted.")
                await self.screenshot_manager.capture_on_error(page, "save_button_not_found")
                raise Exception("Save button not found. Please update selectors.")

            # Wait for save confirmation
            try:
                # Wait for possible success message or page reload
                await page.wait_for_load_state("networkidle", timeout=10000)
                logger.info("Waiting for save confirmation...")

                # Look for success message
                success_selectors = [
                    'text="Success"',
                    'text="Saved"',
                    'text="Configuration saved"',
                    '.success-message',
                    '.alert-success'
                ]

                for selector in success_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=3000)
                        if element:
                            logger.info("Success message detected")
                            break
                    except:
                        continue

            except Exception as e:
                logger.warning(f"Could not confirm save operation: {e}")

            # Capture final screenshot
            await self.screenshot_manager.capture_success(page, "iac_config_complete")

            logger.info("Infrastructure Access Controls configuration completed successfully")
            return True

        except Exception as e:
            logger.error(f"IAC configuration failed: {e}")
            await self.screenshot_manager.capture_on_error(page, "iac_config_error")
            raise
