# Search Button Fix - KNOS Issue RESOLVED ✅

## Problem Summary

After entering the docket number "1:25-CV-01815", the automation was clicking the **KNOS button** instead of the **orange search icon** at the top right.

### Root Cause

The selector `//button[contains(@class, "co_search")]` was matching the KNOS button because it has the class `co_search_advancedSearch_popupButton`, which contains "co_search".

**KNOS Button attributes:**
```
Button class: co_search_advancedSearch_popupButton
Button ID: co_search_advancedSearch_KNOS_button
Button aria-label: Key Nature of Suit (KNOS) Choose KNOS Selections
```

## Solution Applied

### 1. Updated Search Button Selectors

Added explicit exclusion of KNOS buttons in XPath selectors:

**File**: [docket_selection.py](app/src/automation/docket_selection.py:417-429)

```python
search_selectors = [
    # VERY SPECIFIC selectors for the TOP RIGHT orange search icon ONLY
    # Explicitly exclude KNOS buttons - the KNOS button has ID containing "KNOS"
    (By.XPATH, '//button[contains(@class, "co_searchButton") and not(contains(@id, "KNOS"))]'),
    (By.XPATH, '//button[@aria-label="Search Westlaw" and not(contains(@id, "KNOS"))]'),
    (By.XPATH, '//div[contains(@class, "header") or contains(@class, "nav")]//button[contains(@aria-label, "Search") and not(contains(@aria-label, "KNOS"))]'),
    (By.XPATH, '//button[contains(@class, "co_search") and not(contains(@id, "KNOS")) and not(contains(@class, "advancedSearch"))]'),
    (By.XPATH, '//button[@title="Search" and not(contains(@id, "KNOS"))]'),
    (By.CSS_SELECTOR, 'button.co_searchButton:not([id*="KNOS"])'),
    # Look in header/nav specifically, but exclude KNOS
    (By.XPATH, '//header//button[.//*[local-name()="svg"] and not(contains(@id, "KNOS"))]'),
    (By.XPATH, '//nav//button[.//*[local-name()="svg"] and not(contains(@id, "KNOS"))]'),
]
```

### 2. Enhanced Fallback Logic

Updated the button enumeration fallback to check aria-label for KNOS:

**File**: [docket_selection.py](app/src/automation/docket_selection.py:467-470)

```python
# AVOID KNOS explicitly - check ID, class, aria-label, and text
if "knos" in btn_class.lower() or "knos" in btn_id.lower() or "knos" in btn_text.lower() or "knos" in btn_aria.lower():
    logger.info(f"  → Skipping KNOS button")
    continue
```

## Test Results

### ✅ Test Passed Successfully!

**Command**: `python app/test_docket_selection.py`

**Result**: Exit code 0 (Success)

### Logs Confirm Correct Button Clicked

```
FINDING ORANGE SEARCH BUTTON AT TOP RIGHT
Found 6 text input fields
  Input[1]: id='co_search_advancedSearch_DN', name='co_search_advancedSearch_DN'
  ✓ FOUND with id='co_search_advancedSearch_DN', name='co_search_advancedSearch_DN'
✓ SUCCESS: Found docket number input field
✓ Entered: 1:25-CV-01815

Trying search button selector: xpath=//button[contains(@class, "co_searchButton") and not(contains(@id, "KNOS"))]
Trying search button selector: xpath=//button[@aria-label="Search Westlaw" and not(contains(@id, "KNOS"))]
Trying search button selector: xpath=//div[contains(@class, "header") or contains(@class, "nav")]//button[contains(@aria-label, "Search") and not(contains(@aria-label, "KNOS"))]
✓ Found search button with: xpath=//div[contains(@class, "header") or contains(@class, "nav")]//button[contains(@aria-label, "Search") and not(contains(@aria-label, "KNOS"))]

✓ SUCCESS: Found search button!
  Button class:
  Button ID: searchButton
  Button aria-label: Search California Federal District Court Dockets - Southern District
✓ Clicked search button (regular click)
✓ SEARCH COMPLETED

✓✓✓ DOCKET SELECTION TEST PASSED! ✓✓✓
Selected: Dockets by State -> California -> Southern District
Docket Number: 1:25-CV-01815
```

### Screenshot Confirmation

**Screenshot**: [after_clicking_search_20260122_161256.png](app/screenshots/after_clicking_search_20260122_161256.png)

Shows:
- Search box displays: "advanced: DN(1:25-CV-01815)"
- Page shows "Loading, please wait." (search is executing)
- **NO KNOS modal opened** ✅

## Key Changes Summary

### ✅ What Now Works:
1. **Docket number field detection** - Correctly finds `co_search_advancedSearch_DN` (DN = Docket Number)
2. **KNOS button avoidance** - Explicitly excludes buttons with "KNOS" in ID, class, aria-label
3. **Correct search button click** - Clicks button with ID="searchButton" and aria-label="Search..."
4. **Search execution** - Successfully triggers the search instead of opening KNOS modal

### ✅ Selector that Works:
```xpath
//div[contains(@class, "header") or contains(@class, "nav")]//button[contains(@aria-label, "Search") and not(contains(@aria-label, "KNOS"))]
```

This selector:
- Only looks in header/nav area
- Matches buttons with "Search" in aria-label
- Explicitly excludes buttons with "KNOS" in aria-label
- Successfully finds button with ID="searchButton"

## Files Modified

1. **[docket_selection.py](app/src/automation/docket_selection.py)**
   - Lines 417-429: Updated search button selectors with KNOS exclusion
   - Lines 467-470: Enhanced fallback logic to check aria-label for KNOS

## Complete Flow Working Now

```
Content Types
    ↓
Dockets
    ↓
Dockets by State
    ↓
California
    ↓
Southern District
    ↓
Enter Docket Number: 1:25-CV-01815 in field "co_search_advancedSearch_DN"
    ↓
Click CORRECT Search Button (ID="searchButton") ✅
    ↓
Search Results Loading
```

## Summary

✅ **KNOS button issue COMPLETELY RESOLVED**
✅ **Docket number entered in correct field** (DN field, not Participant Name)
✅ **Orange search icon clicked correctly** (not KNOS modal)
✅ **Search executed successfully**
✅ **Test passes with exit code 0**

The automation now correctly:
1. Enters docket number in the "Docket Number" field
2. Avoids all KNOS-related buttons
3. Clicks the orange search icon at the top right
4. Executes the search successfully

**The issue is FIXED!** 🎉
