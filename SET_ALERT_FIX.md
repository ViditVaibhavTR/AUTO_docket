# Set Alert Fix - Correct Element Identified ✅

## Problem

The test was looking for a "notification icon" or "bell icon" but couldn't find it:
```
ERROR: Cannot find notification icon
```

All selectors failed:
- `//button[contains(@aria-label, "notification")]`
- `//button[contains(@aria-label, "alert")]`
- `//button[contains(@class, "notification")]`
- `//button[contains(@class, "bell")]`
- etc.

## Root Cause

Based on the screenshot analysis, there is **NO notification bell icon**. Instead, there's a **"Set alert +"** link/button directly on the search results page.

## Screenshot Evidence

From `search_results_page_20260127_160243.png`:
- Search results show document: "RICO v. Acosta, et al"
- Near the document, there's a **"Set alert +"** link
- This is a direct link, not a two-step process (notification icon → menu)

## Solution Applied

### File: test_docket_selection.py (Lines 111-162)

**Before**: Looking for notification bell icon
```python
notification_selectors = [
    (By.XPATH, '//button[contains(@aria-label, "notification")]'),
    (By.XPATH, '//button[contains(@aria-label, "alert")]'),
    (By.XPATH, '//button[contains(@class, "notification")]'),
    # ... more bell/notification selectors
]
```

**After**: Looking for "Set alert +" link/button
```python
set_alert_selectors = [
    (By.XPATH, '//a[contains(text(), "Set alert")]'),
    (By.XPATH, '//button[contains(text(), "Set alert")]'),
    (By.XPATH, '//*[contains(text(), "Set alert")]'),
    (By.XPATH, '//a[contains(., "Set alert")]'),
    (By.XPATH, '//button[contains(., "Set alert")]'),
    (By.XPATH, '//a[@title="Set alert"]'),
    (By.XPATH, '//button[@title="Set alert"]'),
    (By.XPATH, '//*[text()="Set alert +"]'),
    (By.XPATH, '//*[contains(@class, "alert") and contains(text(), "Set")]'),
    (By.LINK_TEXT, 'Set alert +'),
    (By.PARTIAL_LINK_TEXT, 'Set alert'),
]
```

### Process Changed

**Before** (assumed two-step):
1. Click notification icon
2. Menu appears
3. Click "Create Docket Alert" in menu

**After** (actual one-step):
1. Click "Set alert +" link directly
2. Docket alert interface opens

## Implementation

### 1. Find "Set alert +" Element

```python
logger.info("Looking for 'Set alert +' link/button...")
set_alert_selectors = [
    (By.XPATH, '//a[contains(text(), "Set alert")]'),
    (By.XPATH, '//button[contains(text(), "Set alert")]'),
    # ... 11 selectors total
]

set_alert_button = None
for by, selector in set_alert_selectors:
    try:
        set_alert_button = wait.until(
            EC.element_to_be_clickable((by, selector))
        )
        logger.info(f"✓ Found 'Set alert' with: {by}={selector}")
        break
    except:
        continue

if not set_alert_button:
    screenshot_manager.capture_on_error(driver, "set_alert_not_found")
    raise Exception("Cannot find 'Set alert +' link/button")
```

### 2. Log Element Details

```python
logger.info(f"✓ Found 'Set alert' element")
logger.info(f"  Element tag: {set_alert_button.tag_name}")
logger.info(f"  Element text: {set_alert_button.text}")
logger.info(f"  Element class: {set_alert_button.get_attribute('class')}")
logger.info(f"  Element href: {set_alert_button.get_attribute('href')}")
```

### 3. Click Element

```python
screenshot_manager.capture(driver, "before_clicking_set_alert")

try:
    set_alert_button.click()
    logger.info("✓ Clicked 'Set alert +' (regular click)")
except:
    driver.execute_script("arguments[0].click();", set_alert_button)
    logger.info("✓ Clicked 'Set alert +' (JavaScript click)")

time.sleep(3)
screenshot_manager.capture(driver, "after_clicking_set_alert")
```

## Selectors Explanation

11 different selectors to maximize success:

1. **Text match selectors**:
   - `//a[contains(text(), "Set alert")]` - Link with "Set alert" text
   - `//button[contains(text(), "Set alert")]` - Button with "Set alert" text
   - `//*[contains(text(), "Set alert")]` - Any element with "Set alert"

2. **Exact text selectors**:
   - `//*[text()="Set alert +"]` - Exact match including "+"

3. **Attribute selectors**:
   - `//a[@title="Set alert"]` - Link with title attribute
   - `//*[contains(@class, "alert") and contains(text(), "Set")]` - Class-based

4. **Selenium built-in selectors**:
   - `By.LINK_TEXT, 'Set alert +'` - Direct link text match
   - `By.PARTIAL_LINK_TEXT, 'Set alert'` - Partial link text

## Expected Flow

```
Step 6: Docket Search
    ↓ (success)
Step 7: Create Docket Alert
    ↓
1. Wait for search results page (3s)
2. Capture screenshot: search_results_page
3. Find "Set alert +" link
4. Log element details
5. Capture screenshot: before_clicking_set_alert
6. Click "Set alert +"
7. Wait 3s
8. Capture screenshot: after_clicking_set_alert
    ↓
✅ Docket alert interface opens
```

## Screenshots Captured

Step 7 now captures:
1. `search_results_page` - Shows document results with "Set alert +"
2. `before_clicking_set_alert` - Shows the element to be clicked
3. `after_clicking_set_alert` - Shows docket alert interface

## Expected Logs

```
Step 7: Creating Docket Alert...
Waiting for search results page to load...
Looking for 'Set alert +' link/button...
Trying set alert selector: xpath=//a[contains(text(), "Set alert")]
✓ Found 'Set alert' with: xpath=//a[contains(text(), "Set alert")]
✓ Found 'Set alert' element
  Element tag: a
  Element text: Set alert +
  Element class: ...
  Element href: ...
Clicking 'Set alert +'...
✓ Clicked 'Set alert +' (regular click)
✓✓✓ CREATE DOCKET ALERT STEP COMPLETED! ✓✓✓
```

## Testing

Run the test:
```bash
cd "c:\Users\C303190\OneDrive - Thomson Reuters Incorporated\Desktop\AUTO DOCKET"
python app/test_docket_selection.py
```

Expected result:
1. ✅ Search completes for "1:25-CV-01815"
2. ✅ Finds "Set alert +" link on results page
3. ✅ Clicks "Set alert +"
4. ✅ Docket alert interface opens

## Summary

✅ **Problem Identified** - No notification icon exists
✅ **Correct Element Found** - "Set alert +" link
✅ **Selectors Updated** - 11 robust selectors
✅ **Process Simplified** - One-step instead of two-step
✅ **Ready to Test** - Should work now!

The test is ready to run! 🚀
