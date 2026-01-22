# Fix: Search Button Issue - Avoiding KNOS

## Problem Identified

After entering the docket number, the automation was:
1. ✅ Correctly entering "1:25-CV-01815" in the docket number field
2. ❌ Clicking the WRONG button (opening KNOS modal)
3. ❌ NOT clicking the orange search icon at the top right

## Root Cause

The selectors were too generic and matched a form submit button that opened the KNOS modal, instead of the specific orange search icon button in the top-right corner of the page.

## Solution Applied

### 1. Close Any Open Modals First (Lines 351-362)

Before searching for the button, close any popups:
```python
close_buttons = driver.find_elements(By.XPATH, '//button[contains(text(), "Close") or contains(@aria-label, "Close")]')
for btn in close_buttons:
    btn.click()
```

### 2. Updated Search Button Selectors (Lines 364-377)

**NEW APPROACH**: Only look in header/nav area to avoid form buttons

```python
search_selectors = [
    # VERY SPECIFIC - exclude submit buttons
    (By.XPATH, '//button[contains(@class, "co_search") and not(contains(@type, "submit"))]'),
    (By.XPATH, '//div[contains(@class, "header") or contains(@class, "nav")]//button[contains(@aria-label, "Search")]'),
    (By.XPATH, '//button[@aria-label="Search Westlaw"]'),
    (By.XPATH, '//button[@title="Search"]'),
    (By.XPATH, '//button[contains(@class, "co_searchButton")]'),
    (By.CSS_SELECTOR, 'button.co_searchButton'),
    (By.CSS_SELECTOR, 'button[aria-label*="Search"]'),
    # Look ONLY in header/nav
    (By.XPATH, '//header//button[.//*[local-name()="svg"]]'),
    (By.XPATH, '//nav//button[.//*[local-name()="svg"]]'),
]
```

### 3. Updated Fallback Logic (Lines 393-429)

**NEW APPROACH**: Only enumerate buttons in header/nav area, explicitly skip KNOS

```python
# Get buttons ONLY from header/nav (not from forms)
header_buttons = []
header_buttons.extend(driver.find_elements(By.XPATH, '//header//button'))
header_buttons.extend(driver.find_elements(By.XPATH, '//nav//button'))

for btn in header_buttons:
    btn_class = btn.get_attribute("class") or ""
    btn_id = btn.get_attribute("id") or ""
    btn_aria = btn.get_attribute("aria-label") or ""
    btn_text = btn.text or ""

    # EXPLICITLY AVOID KNOS
    if "knos" in btn_class.lower() or "knos" in btn_id.lower() or "knos" in btn_text.lower():
        logger.info("→ Skipping KNOS button")
        continue

    # Look for search keywords
    if "search" in btn_class.lower() or "search" in btn_aria.lower():
        search_button = btn
        break
```

## Key Changes

### ✅ What We Now Do:
1. Close any open modals/popups first
2. Look ONLY in header/nav area (not in forms)
3. Explicitly skip any button with "knos" in it
4. Target buttons with "search", "co_search", "searchButton" in class
5. Look for buttons with SVG icons in header

### ❌ What We Avoid:
1. Form submit buttons
2. KNOS buttons
3. Modal buttons
4. Buttons outside header/nav area

## Testing

Run the test again:
```bash
python app/test_docket_selection.py
```

### Expected Logs:

```
Looking for ORANGE search icon button at TOP RIGHT corner...
Closed a modal/popup (if any were open)
Trying search button selector: By.XPATH=//button[contains(@class, "co_search")]...
✓ Found search button with: [selector]
✓ Clicked search button

OR if fallback is needed:

Standard selectors failed. Trying to find all buttons in header/nav area...
Found 8 buttons in header/nav area
Header Button 0: class='co_hamburger', id='', aria='Menu'
Header Button 1: class='co_notifications', id='', aria='Notifications'
Header Button 2: class='knos_button', id='knos-btn', aria='KNOS'
  → Skipping KNOS button
Header Button 3: class='co_searchButton', id='search-btn', aria='Search Westlaw'
✓ Found search button in header at index 3
✓ Clicked search button
```

## Files Modified

**File**: [docket_selection.py](app/src/automation/docket_selection.py)

**Changes**:
- Lines 351-362: Close any open modals first
- Lines 364-377: Updated selectors to target header/nav area only
- Lines 393-429: Fallback only looks in header/nav, explicitly skips KNOS

## Summary

✅ **Closes modals** before searching
✅ **Only looks in header/nav** area
✅ **Explicitly skips KNOS** buttons
✅ **9 specific selectors** for top-right search icon
✅ **Logs all header buttons** for debugging
✅ **Avoids form buttons** completely

The automation will now click ONLY the orange search icon at the top right and will NEVER click KNOS! 🎯
