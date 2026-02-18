"""
Aggressive popup blocker for Selenium automation.
Prevents and closes all popups, alerts, modals, and overlays.
"""

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoAlertPresentException, TimeoutException
from src.utils.logger import get_logger
import threading
import time

logger = get_logger(__name__)


class PopupBlocker:
    """Aggressive popup blocker that runs continuously in background"""

    def __init__(self, driver):
        """
        Initialize the popup blocker.

        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
        self.running = False
        self.thread = None
        self.check_count = 0  # Track number of checks
        self.fast_check_limit = 8  # First 8 checks are fast
        self.fast_interval = 0.5  # Fast interval: 0.5 seconds
        self.slow_interval = 3.0  # Slow interval: 3 seconds after first 8 checks

    def inject_popup_prevention_scripts(self):
        """
        Inject JavaScript to prevent and suppress all popups, alerts, and modals.
        This is more aggressive than the basic browser settings.
        """
        try:
            # Comprehensive popup prevention script
            popup_prevention_js = """
            // Suppress all alert/confirm/prompt dialogs
            window.alert = function() { console.log('Alert blocked'); return true; };
            window.confirm = function() { console.log('Confirm blocked'); return true; };
            window.prompt = function() { console.log('Prompt blocked'); return null; };

            // Prevent new windows/tabs
            window.open = function() { console.log('window.open blocked'); return null; };

            // Prevent beforeunload dialogs
            window.onbeforeunload = null;

            // Block notification requests
            if (window.Notification) {
                Notification.requestPermission = function() {
                    console.log('Notification permission blocked');
                    return Promise.reject();
                };
            }

            // Intercept and block all modal-creating events
            document.addEventListener('DOMContentLoaded', function() {
                // Find and remove common modal/overlay classes
                const removeModals = function() {
                    const modalSelectors = [
                        '[class*="modal"]',
                        '[class*="popup"]',
                        '[class*="overlay"]',
                        '[class*="dialog"]',
                        '[id*="modal"]',
                        '[id*="popup"]',
                        '[id*="overlay"]',
                        '[class*="cookie"]',
                        '[class*="consent"]',
                        '[class*="privacy"]',
                        '[class*="banner"]',
                        '[class*="onetrust"]',
                        '[class*="OneTrust"]',
                        '[id*="cookie"]',
                        '[id*="consent"]',
                        '[id*="onetrust"]',
                        '[id*="truste"]'
                    ];

                    modalSelectors.forEach(function(selector) {
                        try {
                            const elements = document.querySelectorAll(selector);
                            elements.forEach(function(el) {
                                // Only remove if it's actually a blocking overlay
                                const style = window.getComputedStyle(el);
                                if (style.position === 'fixed' || style.position === 'absolute') {
                                    if (style.zIndex > 1000) {
                                        console.log('Removing modal/overlay: ' + selector);
                                        el.remove();
                                    }
                                }
                            });
                        } catch(e) {}
                    });
                };

                // Run immediately and periodically
                removeModals();
                setInterval(removeModals, 1000);
            }, false);

            // Mark as initialized
            window.__popup_blocker_initialized = true;
            """

            self.driver.execute_script(popup_prevention_js)
            logger.info("✓ Popup prevention scripts injected")
            return True

        except Exception as e:
            logger.warning(f"Failed to inject popup prevention scripts: {e}")
            return False

    def close_all_alerts(self):
        """Close any alert dialogs that appear"""
        try:
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            logger.info(f"Alert detected: '{alert_text}' - Dismissing...")
            alert.dismiss()  # Try dismiss first
            logger.info("✓ Alert dismissed")
            return True
        except NoAlertPresentException:
            # No alert present - that's good
            return False
        except Exception as e:
            # Try accepting if dismiss fails
            try:
                alert = self.driver.switch_to.alert
                alert.accept()
                logger.info("✓ Alert accepted (dismiss failed)")
                return True
            except:
                return False

    def close_all_modals(self):
        """Find and close all modal dialogs and overlays"""
        try:
            closed_count = 0

            # Common modal close button selectors
            close_selectors = [
                # Close buttons
                '//button[contains(@class, "close")]',
                '//button[contains(@aria-label, "close") or contains(@aria-label, "Close")]',
                '//button[contains(., "×")]',
                '//button[contains(., "✕")]',
                '//span[contains(@class, "close")]',
                '//a[contains(@class, "close")]',

                # Dismiss/Cancel buttons
                '//button[contains(text(), "Dismiss")]',
                '//button[contains(text(), "Cancel")]',
                '//button[contains(text(), "No thanks")]',
                '//button[contains(text(), "Not now")]',
                '//button[contains(text(), "Later")]',
                '//button[contains(text(), "Skip")]',

                # Specific modal dismiss patterns
                '//div[contains(@class, "modal")]//button[contains(@class, "btn-close")]',
                '//div[contains(@class, "popup")]//button[@type="button"]',
                '//div[contains(@role, "dialog")]//button[contains(@aria-label, "Close")]',
            ]

            for selector in close_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                element.click()
                                closed_count += 1
                                logger.info(f"✓ Closed modal using selector: {selector}")
                        except:
                            continue
                except:
                    continue

            # Also try to remove modal backdrops
            try:
                self.driver.execute_script("""
                    var backdrops = document.querySelectorAll('.modal-backdrop, .popup-backdrop, [class*="overlay"]');
                    backdrops.forEach(function(el) {
                        if (window.getComputedStyle(el).zIndex > 1000) {
                            el.remove();
                        }
                    });
                """)
            except:
                pass

            return closed_count > 0

        except Exception as e:
            logger.debug(f"Modal close error: {e}")
            return False

    @staticmethod
    def remove_blocking_overlays(driver):
        """Remove any blocking overlays using JavaScript"""
        try:
            script = """
            // Remove high z-index elements that might be blocking
            var highZIndexElements = document.querySelectorAll('*');
            var removed = 0;

            highZIndexElements.forEach(function(el) {
                try {
                    var style = window.getComputedStyle(el);
                    var zIndex = parseInt(style.zIndex);

                    // Remove if it's a high z-index overlay (lowered threshold to 100)
                    if (zIndex > 100 &&
                        (style.position === 'fixed' || style.position === 'absolute') &&
                        (style.display !== 'none')) {

                        // Check if element is a WestLaw header/navigation element
                        var isWestLawHeader =
                            el.classList.contains('co_topNav') ||
                            el.classList.contains('co_header') ||
                            el.classList.contains('co_siteHeader') ||
                            el.classList.contains('co_globalNav') ||
                            (el.id && (el.id.includes('co_header') || el.id.includes('topNav'))) ||
                            el.closest('.co_topNav') ||
                            el.closest('.co_header') ||
                            el.closest('.co_siteHeader');

                        // Check if element is a form or contains form elements
                        var isFormElement =
                            el.tagName === 'FORM' ||
                            el.tagName === 'INPUT' ||
                            el.tagName === 'TEXTAREA' ||
                            el.tagName === 'SELECT' ||
                            el.tagName === 'BUTTON' ||
                            el.closest('form') ||
                            el.querySelector('input, textarea, select');

                        // Don't remove navigation, headers, or form elements
                        if (!el.closest('header') && !el.closest('nav') && !isWestLawHeader && !isFormElement) {
                            console.log('Removing overlay with z-index: ' + zIndex);
                            el.remove();
                            removed++;
                        }
                    }
                } catch(e) {}
            });

            return removed;
            """

            removed = driver.execute_script(script)
            if removed > 0:
                logger.info(f"✓ Removed {removed} blocking overlay(s)")
                return True
            return False

        except Exception as e:
            logger.debug(f"Overlay removal error: {e}")
            return False

    @staticmethod
    def remove_cookie_banners(driver):
        """Directly remove known cookie consent frameworks by ID/class.
        No getComputedStyle, no z-index checks — just fast element removal."""
        try:
            driver.execute_script("""
                // Remove by exact IDs (OneTrust + common patterns)
                var ids = [
                    'onetrust-banner-sdk', 'onetrust-consent-sdk',
                    'ot-sdk-btn-floating', 'onetrust-pc-dark-filter',
                    'CookieConsentBanner', 'cookie-banner', 'cookieBanner',
                    'cookie-consent', 'privacy-banner', 'truste-consent-track'
                ];
                ids.forEach(function(id) {
                    var el = document.getElementById(id);
                    if (el) { el.remove(); }
                });

                // Remove by class selectors
                var selectors = [
                    '.optanon-alert-box-wrapper', '.onetrust-pc-dark-filter',
                    '.cookie-notice', '.privacy-banner', '.cookie-consent-banner',
                    '#ot-sdk-btn-floating', '.ot-sdk-container'
                ];
                selectors.forEach(function(sel) {
                    document.querySelectorAll(sel).forEach(function(el) { el.remove(); });
                });
            """)
        except Exception:
            pass

    def block_popups_once(self):
        """
        Run one cycle of popup blocking.
        Returns True if any popups were blocked.
        """
        blocked = False

        # 1. Close alerts
        if self.close_all_alerts():
            blocked = True

        # 2. Close modals
        if self.close_all_modals():
            blocked = True

        # 3. Remove overlays
        if self.remove_blocking_overlays(self.driver):
            blocked = True

        # 4. Remove cookie consent banners (direct ID/class removal)
        self.remove_cookie_banners(self.driver)

        # 5. Re-inject prevention scripts (in case page reloaded)
        #    Also reset fast check counter so new pages get aggressive blocking
        try:
            initialized = self.driver.execute_script("return window.__popup_blocker_initialized || false;")
            if not initialized:
                self.inject_popup_prevention_scripts()
                if self.check_count >= self.fast_check_limit:
                    logger.info("New page detected — restarting fast popup checks")
                    self.check_count = 0
        except:
            pass

        return blocked

    def _background_blocker_loop(self):
        """Background thread loop that continuously blocks popups with adaptive interval"""
        logger.info("Popup blocker background thread started")
        logger.info(f"First {self.fast_check_limit} checks at {self.fast_interval}s intervals, then {self.slow_interval}s")

        while self.running:
            try:
                self.block_popups_once()
                self.check_count += 1

                # Use fast interval for first 4 checks, then slow down
                if self.check_count <= self.fast_check_limit:
                    interval = self.fast_interval
                    if self.check_count == self.fast_check_limit:
                        logger.info(f"✓ Completed {self.fast_check_limit} fast checks, switching to {self.slow_interval}s interval")
                else:
                    interval = self.slow_interval

                time.sleep(interval)
            except Exception as e:
                # Don't log every error, just continue
                pass

        logger.info("Popup blocker background thread stopped")

    def start_background_blocking(self):
        """Start background thread to continuously block popups"""
        if self.running:
            logger.warning("Popup blocker already running")
            return

        logger.info("Starting background popup blocker...")
        self.running = True
        self.thread = threading.Thread(target=self._background_blocker_loop, daemon=True)
        self.thread.start()
        logger.info("✓ Background popup blocker started")

    def stop_background_blocking(self):
        """Stop background popup blocking thread"""
        if not self.running:
            return

        logger.info("Stopping background popup blocker...")
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("✓ Background popup blocker stopped")

    def __enter__(self):
        """Context manager entry"""
        self.inject_popup_prevention_scripts()
        self.start_background_blocking()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_background_blocking()
