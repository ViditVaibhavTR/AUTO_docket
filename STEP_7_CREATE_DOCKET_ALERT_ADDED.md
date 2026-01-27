# Step 7: Create Docket Alert - Test Added ✅

## Summary

Added **Step 7** to test_docket_selection.py as a **separate process** (not clubbed with previous steps).

After the docket number search completes, this step:
1. Finds the notification icon below the search bar
2. Clicks on it
3. Finds "Create Docket Alert" option
4. Clicks on it

## Complete Test Flow

```
Step 1: Start browser
Step 2: Navigate to routing page
Step 3: Configure Gateway
Step 4: Configure IAC
Step 5: Login to WestLaw Precision
Step 6: Docket selection + Search
    ↓ (if success)
Step 7: Create Docket Alert ← NEW! (SEPARATE)
```

## Changes Made

### File: test_docket_selection.py

**Lines 92-209**: Added Step 7 as a separate block that executes only after Step 6 succeeds

## Step 7 Implementation

### 1. Wait for Search Results Page

```python
logger.info("Waiting for search results page to load...")
time.sleep(3)
screenshot_manager.capture(driver, "search_results_page")
```

### 2. Find Notification Icon

Uses multiple selectors to find the notification icon below the search bar:

```python
notification_selectors = [
    (By.XPATH, '//button[contains(@aria-label, "notification")]'),
    (By.XPATH, '//button[contains(@aria-label, "alert")]'),
    (By.XPATH, '//button[contains(@class, "notification")]'),
    (By.XPATH, '//button[contains(@class, "alert")]'),
    (By.CSS_SELECTOR, 'button[aria-label*="notification"]'),
    (By.CSS_SELECTOR, 'button[aria-label*="alert"]'),
    (By.XPATH, '//button[.//*[local-name()="svg" and contains(@class, "notification")]]'),
    (By.XPATH, '//button[.//*[local-name()="svg" and contains(@class, "bell")]]'),
]
```

Logs button attributes for debugging:
```python
logger.info(f"  Button class: {notification_icon.get_attribute('class')}")
logger.info(f"  Button aria-label: {notification_icon.get_attribute('aria-label')}")
```

### 3. Click Notification Icon

```python
screenshot_manager.capture(driver, "before_clicking_notification_icon")

try:
    notification_icon.click()
    logger.info("✓ Clicked notification icon (regular click)")
except:
    driver.execute_script("arguments[0].click();", notification_icon)
    logger.info("✓ Clicked notification icon (JavaScript click)")

time.sleep(2)
screenshot_manager.capture(driver, "after_clicking_notification_icon")
```

### 4. Find "Create Docket Alert" Option

Uses multiple selectors to find the option:

```python
create_alert_selectors = [
    (By.XPATH, '//button[contains(text(), "Create Docket Alert")]'),
    (By.XPATH, '//a[contains(text(), "Create Docket Alert")]'),
    (By.XPATH, '//*[contains(text(), "Create Docket Alert")]'),
    (By.XPATH, '//button[contains(., "Create Docket Alert")]'),
    (By.XPATH, '//a[contains(., "Create Docket Alert")]'),
    (By.CSS_SELECTOR, 'button:has-text("Create Docket Alert")'),
]
```

Logs element details:
```python
logger.info(f"  Element tag: {create_alert_button.tag_name}")
logger.info(f"  Element text: {create_alert_button.text}")
logger.info(f"  Element class: {create_alert_button.get_attribute('class')}")
```

### 5. Click "Create Docket Alert"

```python
screenshot_manager.capture(driver, "before_clicking_create_alert")

try:
    create_alert_button.click()
    logger.info("✓ Clicked 'Create Docket Alert' (regular click)")
except:
    driver.execute_script("arguments[0].click();", create_alert_button)
    logger.info("✓ Clicked 'Create Docket Alert' (JavaScript click)")

time.sleep(3)
screenshot_manager.capture(driver, "after_clicking_create_alert")
```

## Screenshots Captured

Step 7 captures these screenshots:
1. `search_results_page` - Page after docket search
2. `before_clicking_notification_icon` - Shows notification icon location
3. `after_clicking_notification_icon` - Shows menu that appears
4. `before_clicking_create_alert` - Shows "Create Docket Alert" option
5. `after_clicking_create_alert` - Result after clicking

## Error Handling

If any step fails:
- Screenshot captured: `notification_icon_not_found` or `create_docket_alert_not_found`
- Exception raised with clear message
- Browser kept open for 10 seconds to inspect

## Testing

Run the test:
```bash
cd "c:\Users\C303190\OneDrive - Thomson Reuters Incorporated\Desktop\AUTO DOCKET"
python app/test_docket_selection.py
```

Expected flow:
1. ✅ Login
2. ✅ Configure Gateway
3. ✅ Configure IAC
4. ✅ Navigate: Content Types → Dockets
5. ✅ Select: California
6. ✅ Select: Southern District
7. ✅ Enter: 1:25-CV-01815
8. ✅ Click: Search button
9. ✅ Click: Notification icon ← NEW
10. ✅ Click: "Create Docket Alert" ← NEW

## Logs Output

```
Step 6: Attempting to select docket...
Testing: Dockets by State -> California -> Southern District -> 1:25-CV-01815
✓✓✓ DOCKET SELECTION TEST PASSED! ✓✓✓
Selected: Dockets by State -> California -> Southern District
Docket Number: 1:25-CV-01815

Step 7: Creating Docket Alert...
Waiting for search results page to load...
Looking for notification icon below search bar...
Trying notification selector: xpath=//button[contains(@aria-label, "notification")]
✓ Found notification icon with: xpath=...
  Button class: ...
  Button aria-label: ...
Clicking notification icon...
✓ Clicked notification icon (regular click)
Looking for 'Create Docket Alert' option...
Trying create alert selector: xpath=//button[contains(text(), "Create Docket Alert")]
✓ Found 'Create Docket Alert' with: xpath=...
  Element tag: button
  Element text: Create Docket Alert
  Element class: ...
Clicking 'Create Docket Alert'...
✓ Clicked 'Create Docket Alert' (regular click)
✓✓✓ CREATE DOCKET ALERT STEP COMPLETED! ✓✓✓
```

## Key Features

✅ **Separate step** - Only runs after Step 6 succeeds
✅ **Not clubbed** - Independent execution block
✅ **Multiple selectors** - Robust element detection
✅ **Screenshots** - Visual debugging at each step
✅ **Error handling** - Clear error messages
✅ **Logging** - Detailed element attributes
✅ **Click fallback** - JavaScript click if regular fails

## Next Steps

After this test succeeds:
1. Check logs to identify working selectors
2. Check screenshots to verify correct elements clicked
3. Optimize by prioritizing working selectors
4. Add to Streamlit chatbot as Phase 5

## Summary

✅ **Step 7 added** - Create Docket Alert functionality
✅ **Separate process** - Not clubbed with previous steps
✅ **Ready to test** - Run test_docket_selection.py
✅ **Full logging** - Detailed debugging information
✅ **Screenshot support** - Visual verification at each step

The test is ready to run! 🚀
