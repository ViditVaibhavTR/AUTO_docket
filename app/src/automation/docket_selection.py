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

    def select_docket(self, driver, category=None, specific_docket=None, district=None, docket_number=None) -> bool:
        """
        Select "Dockets" from Content Types in WestLaw Precision,
        and optionally select a specific category, docket, district, and search by docket number.

        Args:
            driver: Selenium WebDriver object
            category: Optional category name (e.g., "Dockets by State")
            specific_docket: Optional specific docket name (e.g., "California")
            district: Optional district name (e.g., "Southern District")
            docket_number: Optional docket number to search (e.g., "1:25-CV-01815")

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
            if district:
                logger.info(f"District: {district}")
            if docket_number:
                logger.info(f"Docket Number: {docket_number}")

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

                # Wait for specific docket options to appear after page navigation
                logger.info(f"Waiting for specific dockets page to load...")
                time.sleep(3)  # Increased wait time for page navigation

                # Find and click the specific docket (try multiple selectors)
                logger.info(f"Looking for specific docket: {specific_docket}")

                # Take screenshot before searching
                self.screenshot_manager.capture(driver, "before_searching_specific_docket")

                try:
                    docket_wait = WebDriverWait(driver, 15)

                    # Try multiple selectors for state links
                    state_selectors = [
                        f'//a[text()="{specific_docket}"]',  # Exact match for link
                        f'//a[contains(text(), "{specific_docket}")]',  # Contains match for link
                        f'//*[@href and contains(text(), "{specific_docket}")]',  # Any element with href containing text
                        f'//*[text()="{specific_docket}"]',  # Exact text match
                        f'//*[contains(text(), "{specific_docket}")]'  # General contains match
                    ]

                    docket_element = None
                    for selector in state_selectors:
                        try:
                            logger.info(f"Trying state selector: {selector}")
                            docket_element = docket_wait.until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            logger.info(f"✓ Found specific docket with: {selector}")
                            break
                        except Exception as e:
                            logger.debug(f"Selector failed: {selector} - {str(e)}")
                            continue

                    if not docket_element:
                        logger.error("Failed to find specific docket with any selector")
                        self.screenshot_manager.capture_on_error(driver, "specific_docket_not_found")
                        raise Exception(f"Cannot find state: {specific_docket}")

                    logger.info(f"✓ Found specific docket: {specific_docket}")

                    # Scroll into view before clicking
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", docket_element)
                    time.sleep(0.5)

                    self.screenshot_manager.capture(driver, "before_clicking_specific_docket")
                    driver.execute_script("arguments[0].click();", docket_element)
                    logger.info(f"✓ Clicked on specific docket: {specific_docket}")
                    time.sleep(2)
                    self.screenshot_manager.capture(driver, "after_clicking_specific_docket")
                except Exception as e:
                    logger.error(f"Failed to find specific docket '{specific_docket}': {str(e)}")
                    self.screenshot_manager.capture_on_error(driver, "specific_docket_not_found")
                    raise

                # If district is provided, select the district
                if district:
                    # Wait for district options to appear
                    logger.info(f"Waiting for district options to load...")
                    time.sleep(3)

                    # Find and click the district
                    logger.info(f"Looking for district: {district}")
                    self.screenshot_manager.capture(driver, "before_searching_district")

                    try:
                        district_wait = WebDriverWait(driver, 15)

                        # Try multiple selectors for district links
                        district_selectors = [
                            f'//a[text()="{district}"]',  # Exact match for link
                            f'//a[contains(text(), "{district}")]',  # Contains match for link
                            f'//*[@href and contains(text(), "{district}")]',  # Any element with href
                            f'//*[text()="{district}"]',  # Exact text match
                            f'//*[contains(text(), "{district}")]'  # General contains match
                        ]

                        district_element = None
                        for selector in district_selectors:
                            try:
                                logger.info(f"Trying district selector: {selector}")
                                district_element = district_wait.until(
                                    EC.element_to_be_clickable((By.XPATH, selector))
                                )
                                logger.info(f"✓ Found district with: {selector}")
                                break
                            except Exception as e:
                                logger.debug(f"Selector failed: {selector} - {str(e)}")
                                continue

                        if not district_element:
                            logger.error("Failed to find district with any selector")
                            self.screenshot_manager.capture_on_error(driver, "district_not_found")
                            raise Exception(f"Cannot find district: {district}")

                        logger.info(f"✓ Found district: {district}")

                        # Scroll into view before clicking
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", district_element)
                        time.sleep(0.5)

                        self.screenshot_manager.capture(driver, "before_clicking_district")
                        driver.execute_script("arguments[0].click();", district_element)
                        logger.info(f"✓ Clicked on district: {district}")
                        time.sleep(2)
                        self.screenshot_manager.capture(driver, "after_clicking_district")
                    except Exception as e:
                        logger.error(f"Failed to find district '{district}': {str(e)}")
                        self.screenshot_manager.capture_on_error(driver, "district_selection_error")
                        raise

                # If docket_number is provided, search for the docket
                if docket_number:
                    # Wait for docket number input field to appear
                    logger.info(f"Waiting for docket number input field...")
                    time.sleep(1)  # Reduced from 3s - using explicit waits in selectors

                    # Find and fill the docket number input field
                    logger.info("=" * 60)
                    logger.info("FINDING DOCKET NUMBER INPUT FIELD")
                    logger.info("=" * 60)
                    logger.info(f"Taking screenshot before searching for input...")
                    self.screenshot_manager.capture(driver, "before_docket_number_input")

                    try:
                        docket_wait = WebDriverWait(driver, 5)  # Reduced from 15s - working selectors are first

                        # Log ALL text inputs on the page for debugging
                        logger.info("LISTING ALL TEXT INPUTS ON PAGE:")
                        all_inputs = driver.find_elements(By.XPATH, '//input[@type="text"]')
                        logger.info(f"Found {len(all_inputs)} text input fields")

                        for i, inp in enumerate(all_inputs):
                            try:
                                inp_id = inp.get_attribute("id") or "NO_ID"
                                inp_name = inp.get_attribute("name") or "NO_NAME"
                                inp_placeholder = inp.get_attribute("placeholder") or "NO_PLACEHOLDER"
                                logger.info(f"  Input[{i}]: id='{inp_id}', name='{inp_name}', placeholder='{inp_placeholder}'")
                            except:
                                pass

                        # Try SPECIFIC selectors for the actual Docket Number field on the LEFT
                        logger.info("\nTrying specific selectors for 'Docket Number' field...")
                        input_selectors = [
                            # PRIORITY: Known working selectors first for speed
                            (By.ID, "co_search_advancedSearch_DN"),  # DN = Docket Number (WORKING)
                            (By.NAME, "co_search_advancedSearch_DN"),  # DN = Docket Number (WORKING)
                            (By.XPATH, '//label[contains(text(), "Docket Number")]/..//input'),  # WORKING
                            # Fallback selectors
                            (By.ID, "docketNumber"),
                            (By.NAME, "docketNumber"),
                            (By.XPATH, '//label[text()="Docket Number"]/following-sibling::input'),
                            (By.XPATH, '//input[@placeholder="Docket Number"]'),
                            (By.XPATH, '//input[@id="docketNumber"]'),
                        ]

                        input_element = None
                        for by, selector in input_selectors:
                            try:
                                logger.info(f"  Trying: {by}={selector}")
                                input_element = docket_wait.until(
                                    EC.presence_of_element_located((by, selector))
                                )
                                inp_id = input_element.get_attribute("id")
                                inp_name = input_element.get_attribute("name")
                                logger.info(f"  ✓ FOUND with id='{inp_id}', name='{inp_name}'")
                                break
                            except Exception as e:
                                logger.debug(f"  ✗ Failed: {str(e)[:50]}")
                                continue

                        if not input_element:
                            logger.error("SPECIFIC SELECTORS FAILED! Trying to find by label...")
                            # Find the label "Docket Number" and get nearby input
                            try:
                                logger.info("Looking for 'Docket Number' label...")
                                all_labels = driver.find_elements(By.TAG_NAME, "label")
                                for label in all_labels:
                                    if "docket number" in label.text.lower() and "participant" not in label.text.lower():
                                        logger.info(f"Found label: '{label.text}'")
                                        # Try to get input via 'for' attribute
                                        label_for = label.get_attribute("for")
                                        if label_for:
                                            input_element = driver.find_element(By.ID, label_for)
                                            logger.info(f"✓ Found input via label 'for' attribute: {label_for}")
                                            break
                            except Exception as e:
                                logger.error(f"Label search failed: {e}")

                        if not input_element:
                            logger.error("=" * 60)
                            logger.error("CRITICAL: CANNOT FIND DOCKET NUMBER INPUT FIELD")
                            logger.error("=" * 60)
                            self.screenshot_manager.capture_on_error(driver, "docket_input_not_found_CRITICAL")
                            raise Exception("Cannot find docket number input field")

                        logger.info("=" * 60)
                        logger.info(f"✓ SUCCESS: Found docket number input field")
                        logger.info(f"  ID: {input_element.get_attribute('id')}")
                        logger.info(f"  Name: {input_element.get_attribute('name')}")
                        logger.info(f"  Placeholder: {input_element.get_attribute('placeholder')}")
                        logger.info("=" * 60)

                        # Clear and enter the docket number
                        logger.info(f"Entering docket number: {docket_number}")
                        input_element.clear()
                        input_element.send_keys(docket_number)
                        logger.info(f"✓ Entered: {docket_number}")
                        time.sleep(0.5)  # Reduced from 1s - just ensure text is entered
                        logger.info("Taking screenshot AFTER entering docket number...")
                        self.screenshot_manager.capture(driver, "after_entering_docket_number")

                        # Find and click ONLY the orange search icon at top right (NOT KNOS or any modal buttons)
                        logger.info("=" * 60)
                        logger.info("FINDING ORANGE SEARCH BUTTON AT TOP RIGHT")
                        logger.info("=" * 60)
                        logger.info("Taking screenshot BEFORE searching for button...")
                        self.screenshot_manager.capture(driver, "before_searching_for_search_button")

                        # First, make sure any modals are closed
                        try:
                            close_buttons = driver.find_elements(By.XPATH, '//button[contains(text(), "Close") or contains(@aria-label, "Close")]')
                            if close_buttons:
                                logger.info(f"Found {len(close_buttons)} close buttons, closing modals...")
                            for btn in close_buttons:
                                try:
                                    btn.click()
                                    logger.info("✓ Closed a modal/popup")
                                    time.sleep(0.5)
                                except:
                                    pass
                        except:
                            pass

                        search_selectors = [
                            # PRIORITY: Known working selectors first for speed
                            (By.ID, "searchButton"),  # Direct ID (FASTEST - WORKING)
                            (By.XPATH, '//button[@id="searchButton"]'),  # Direct ID xpath (WORKING)
                            (By.XPATH, '//div[contains(@class, "header") or contains(@class, "nav")]//button[contains(@aria-label, "Search") and not(contains(@aria-label, "KNOS"))]'),  # WORKING
                            # Fallback selectors
                            (By.XPATH, '//button[contains(@class, "co_searchButton") and not(contains(@id, "KNOS"))]'),
                            (By.XPATH, '//button[@aria-label="Search Westlaw" and not(contains(@id, "KNOS"))]'),
                            (By.XPATH, '//button[contains(@class, "co_search") and not(contains(@id, "KNOS")) and not(contains(@class, "advancedSearch"))]'),
                            (By.XPATH, '//button[@title="Search" and not(contains(@id, "KNOS"))]'),
                            (By.CSS_SELECTOR, 'button.co_searchButton:not([id*="KNOS"])'),
                            # Look in header/nav specifically, but exclude KNOS
                            (By.XPATH, '//header//button[.//*[local-name()="svg"] and not(contains(@id, "KNOS"))]'),
                            (By.XPATH, '//nav//button[.//*[local-name()="svg"] and not(contains(@id, "KNOS"))]'),
                        ]

                        search_button = None
                        for by, selector in search_selectors:
                            try:
                                logger.info(f"Trying search button selector: {by}={selector}")
                                search_button = docket_wait.until(
                                    EC.element_to_be_clickable((by, selector))
                                )
                                logger.info(f"✓ Found search button with: {by}={selector}")
                                break
                            except Exception as e:
                                logger.debug(f"Selector failed: {by}={selector} - {str(e)}")
                                continue

                        # If standard selectors didn't work, try finding all buttons and log them
                        if not search_button:
                            logger.warning("Standard selectors failed. Trying to find all buttons in header/nav area...")
                            try:
                                # Get buttons specifically from header/nav to avoid KNOS and form buttons
                                header_buttons = []
                                try:
                                    header_buttons.extend(driver.find_elements(By.XPATH, '//header//button'))
                                    header_buttons.extend(driver.find_elements(By.XPATH, '//nav//button'))
                                except:
                                    pass

                                logger.info(f"Found {len(header_buttons)} buttons in header/nav area")

                                # Look through header buttons for the search icon
                                for i, btn in enumerate(header_buttons):
                                    try:
                                        btn_class = btn.get_attribute("class") or ""
                                        btn_id = btn.get_attribute("id") or ""
                                        btn_aria = btn.get_attribute("aria-label") or ""
                                        btn_text = btn.text or ""
                                        logger.info(f"Header Button {i}: class='{btn_class}', id='{btn_id}', aria='{btn_aria}', text='{btn_text}'")

                                        # AVOID KNOS explicitly - check ID, class, aria-label, and text
                                        if "knos" in btn_class.lower() or "knos" in btn_id.lower() or "knos" in btn_text.lower() or "knos" in btn_aria.lower():
                                            logger.info(f"  → Skipping KNOS button")
                                            continue

                                        # Look for search-related keywords
                                        if any(keyword in btn_class.lower() for keyword in ["search", "co_search", "searchbutton"]) or \
                                           "search" in btn_aria.lower():
                                            search_button = btn
                                            logger.info(f"✓ Found search button in header at index {i}")
                                            break
                                    except:
                                        continue
                            except Exception as e:
                                logger.error(f"Failed to enumerate header buttons: {e}")

                        if not search_button:
                            logger.error("=" * 60)
                            logger.error("CRITICAL: CANNOT FIND SEARCH BUTTON")
                            logger.error("=" * 60)
                            self.screenshot_manager.capture_on_error(driver, "search_button_not_found_CRITICAL")
                            raise Exception("Cannot find orange search button")

                        logger.info("=" * 60)
                        logger.info("✓ SUCCESS: Found search button!")
                        logger.info(f"  Button class: {search_button.get_attribute('class')}")
                        logger.info(f"  Button ID: {search_button.get_attribute('id')}")
                        logger.info(f"  Button aria-label: {search_button.get_attribute('aria-label')}")
                        logger.info("=" * 60)

                        logger.info("Taking screenshot BEFORE clicking search button...")
                        self.screenshot_manager.capture(driver, "before_clicking_search")

                        # Try regular click first, then JavaScript click if needed
                        logger.info("Clicking the orange search button...")
                        try:
                            search_button.click()
                            logger.info(f"✓ Clicked search button (regular click)")
                        except Exception as e:
                            logger.warning(f"Regular click failed: {e}")
                            logger.warning("Trying JavaScript click...")
                            driver.execute_script("arguments[0].click();", search_button)
                            logger.info(f"✓ Clicked search button (JavaScript click)")

                        logger.info("Waiting 2 seconds for search results...")
                        time.sleep(2)  # Reduced from 3s - just ensure click is registered
                        logger.info("Taking screenshot AFTER clicking search...")
                        self.screenshot_manager.capture(driver, "after_clicking_search")
                        logger.info("=" * 60)
                        logger.info("✓ SEARCH COMPLETED")
                        logger.info("=" * 60)

                    except Exception as e:
                        logger.error(f"Failed to search docket number '{docket_number}': {str(e)}")
                        self.screenshot_manager.capture_on_error(driver, "docket_search_error")
                        raise

            logger.info("Docket selection completed successfully")
            return True

        except Exception as e:
            logger.error(f"Docket selection failed: {e}")
            self.screenshot_manager.capture_on_error(driver, "docket_selection_error")
            raise
