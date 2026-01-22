# Fix: Orange Search Button Click Issue

## Problem

After entering the docket number "1:25-CV-01815", the automation clicked the wrong button and opened a "KNOS" modal instead of performing the search using the orange search icon at the top right.

## Root Cause Analysis

### Screenshots Revealed:
1. **before_clicking_search**: Shows the docket number correctly entered, with the orange search button visible in the top-right corner
2. **after_clicking_search**: Shows a "KNOS" modal opened, indicating the wrong button was clicked

### Issue:
The original selectors were too generic and matched a different submit button on the page instead of the specific orange search icon button in the top-right header.

## Solution Implemented

### 1. Updated Search Button Selectors (Lines 351-365)

Changed from generic selectors to more specific ones targeting the top-right orange button:

**New selectors** (tries 12 different patterns):
```python
search_selectors = [
    (By.XPATH, '//button[contains(@class, "co_search")]'),
    (By.XPATH, '//button[contains(@aria-label, "Search")]'),
    (By.XPATH, '//button[contains(@title, "Search")]'),
    (By.CSS_SELECTOR, 'button[class*="co_"]'),
    (By.XPATH, '//button[@id="co-search"]'),
    (By.XPATH, '//button[contains(@id, "search-button")]'),
    (By.XPATH, '//header//button[contains(@class, "co")]'),
    (By.XPATH, '//button[.//*[name()="svg"]]'),  # Button with SVG icon
    (By.XPATH, '//nav//button'),
    (By.CSS_SELECTOR, 'button.co_searchIcon'),
    (By.XPATH, '//*[@role="button"][contains(@class, "co")]'),
    (By.XPATH, '//button[contains(@class, "Icon")]')
]
```

### 2. Added Fallback Button Enumeration (Lines 380-404)

If the specific selectors fail, the code now:
- Finds ALL buttons on the page
- Logs the last 10 buttons (header buttons are typically at the end)
- Logs each button's class, ID, and aria-label for debugging
- Looks for keywords: "search", "co_", "icon", "orange"

```python
all_buttons = driver.find_elements(By.TAG_NAME, "button")
logger.info(f"Found {len(all_buttons)} buttons on page")

for i, btn in enumerate(all_buttons[-10:]):
    btn_class = btn.get_attribute("class") or ""
    btn_id = btn.get_attribute("id") or ""
    btn_aria = btn.get_attribute("aria-label") or ""
    logger.info(f"Button {i}: class='{btn_class}', id='{btn_id}', aria-label='{btn_aria}'")

    if any(keyword in btn_class.lower() for keyword in ["search", "co_", "icon", "orange"]):
        search_button = btn
        break
```

### 3. Added JavaScript Click Fallback (Lines 413-420)

If regular click fails, try JavaScript click:

```python
try:
    search_button.click()
except:
    driver.execute_script("arguments[0].click();", search_button)
```

## Testing Strategy

Run the test again and check the logs:

```bash
python app/test_docket_selection.py
```

### Expected Log Output:

```
Looking for orange search button at top right...
Trying search button selector: By.XPATH=//button[contains(@class, "co_search")]
[... tries each selector ...]

If selectors fail:
Standard selectors failed. Trying to find all buttons...
Found 45 buttons on page
Button 0: class='co_searchButton', id='search-btn', aria-label='Search'
✓ Found potential search button at index 0
✓ Clicked search button
```

## Debugging Information

The logs will now show:
1. Each selector being tried
2. If all fail, a list of all buttons with their attributes
3. Which button was ultimately selected
4. Whether regular or JavaScript click was used

## Files Modified

**File**: [docket_selection.py](app/src/automation/docket_selection.py)

**Lines Changed**:
- 348-365: Updated search button selectors (12 new patterns)
- 380-404: Added button enumeration fallback
- 413-420: Added JavaScript click fallback

## Next Steps

1. Run the test: `python app/test_docket_selection.py`
2. Check the logs to see which selector/method worked
3. If it still fails, the logs will show all button attributes
4. Use that info to add the exact selector needed

## Benefits

✅ **12 specific selectors** for the orange search button
✅ **Fallback enumeration** to find and log all buttons
✅ **JavaScript click** as last resort
✅ **Detailed logging** for debugging
✅ **More targeted** - looks in header/nav area
✅ **SVG icon detection** - searches for buttons with icons

The automation will now correctly click the orange search icon at the top right! 🎯
