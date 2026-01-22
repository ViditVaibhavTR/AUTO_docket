# Docket Number Search Feature Added ✅

## Overview

Added support for entering a docket number in the search field and clicking the orange search button. The automation now handles a **four-level hierarchy**:

1. **Dockets by State** (e.g., "California")
2. **State** (e.g., "California")
3. **District** (e.g., "Southern District")
4. **Docket Number** (e.g., "1:25-CV-01815") + Search

## Complete Flow

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
[Enter Docket Number: 1:25-CV-01815]
    ↓
[Click Orange Search Button 🔍]
    ↓
Search Results
```

## Implementation Details

### Files Modified

#### 1. [docket_selection.py](app/src/automation/docket_selection.py)

**Function signature updated** (Line 23):
```python
def select_docket(self, driver, category=None, specific_docket=None, district=None, docket_number=None)
```

**New parameter**: `docket_number` - Optional docket number to search (e.g., "1:25-CV-01815")

**Docket number search logic added** (Lines 298-389):
- Waits 3 seconds for input field to appear
- Tries 6 different selectors for input field
- Clears field and enters docket number
- Tries 8 different selectors for search button
- Clicks search button
- Takes 4 screenshots:
  - `before_docket_number_input`
  - `after_entering_docket_number`
  - `before_clicking_search`
  - `after_clicking_search`
- Error screenshots:
  - `docket_input_not_found`
  - `search_button_not_found`
  - `docket_search_error`

#### 2. [test_docket_selection.py](app/test_docket_selection.py)

**Test updated** (Lines 72-82):
```python
docket_selector.select_docket(
    driver,
    category="Dockets by State",
    specific_docket="California",
    district="Southern District",
    docket_number="1:25-CV-01815"  # NEW
)
```

**Test path**: Content Types → Dockets → Dockets by State → California → Southern District → 1:25-CV-01815 → Search

## Input Field Selectors

The code tries these selectors for the docket number input field:

1. `(By.ID, "docket-number")` - ID selector
2. `(By.NAME, "docket")` - Name attribute
3. `(By.XPATH, '//input[@placeholder="Docket Number"]')` - Placeholder text
4. `(By.XPATH, '//input[@type="text"]')` - Text input type
5. `(By.XPATH, '//input[contains(@class, "docket")]')` - Class contains "docket"
6. `(By.CSS_SELECTOR, 'input[type="text"]')` - CSS selector

## Search Button Selectors

The code tries these selectors for the orange search button:

1. `(By.XPATH, '//button[contains(@class, "search")]')` - Class contains "search"
2. `(By.XPATH, '//button[@type="submit"]')` - Submit button
3. `(By.XPATH, '//button[contains(@style, "orange")]')` - Style contains "orange"
4. `(By.XPATH, '//button[contains(., "Search")]')` - Text contains "Search"
5. `(By.CSS_SELECTOR, 'button.search')` - CSS class
6. `(By.CSS_SELECTOR, 'button[type="submit"]')` - CSS submit
7. `(By.XPATH, '//input[@type="submit"]')` - Input submit
8. `(By.XPATH, '//*[@role="button"][contains(@class, "search")]')` - Role=button

## Testing

### Run the test script:

```bash
cd "c:\Users\C303190\OneDrive - Thomson Reuters Incorporated\Desktop\AUTO DOCKET"
python app/test_docket_selection.py
```

### Expected Flow:

```
Step 1: Starting browser... ✓
Step 2: Navigating to routing page... ✓
Step 3: Configuring Gateway... ✓
Step 4: Configuring IAC... ✓
Step 5: Logging into WestLaw Precision... ✓

NOW TESTING DOCKET SELECTION...

Step 6: Attempting to select docket...
Testing: Dockets by State -> California -> Southern District -> 1:25-CV-01815

Starting docket selection...
Category: Dockets by State
Specific docket: California
District: Southern District
Docket Number: 1:25-CV-01815

✓ Clicked Content Types tab
✓ Clicked Dockets option
✓ Clicked on category: Dockets by State
✓ Clicked on specific docket: California
✓ Clicked on district: Southern District

Waiting for docket number input field...
Looking for docket number input field...
✓ Found input field with: [selector]
✓ Entered docket number: 1:25-CV-01815

Looking for search button...
✓ Found search button with: [selector]
✓ Clicked search button

✓✓✓ DOCKET SELECTION TEST PASSED! ✓✓✓
Selected: Dockets by State -> California -> Southern District
Docket Number: 1:25-CV-01815
```

## Screenshots Generated

### Phase 1: Content Types → Dockets (5 screenshots)
1. `before_content_types_search`
2. `before_clicking_content_types`
3. `after_clicking_content_types`
4. `after_clicking_dockets`

### Phase 2: Category → State (5 screenshots)
5. `before_clicking_category`
6. `after_clicking_category`
7. `before_searching_specific_docket`
8. `before_clicking_specific_docket`
9. `after_clicking_specific_docket`

### Phase 3: District (3 screenshots)
10. `before_searching_district`
11. `before_clicking_district`
12. `after_clicking_district`

### Phase 4: Docket Number Search (4 screenshots - NEW)
13. `before_docket_number_input` ← NEW
14. `after_entering_docket_number` ← NEW
15. `before_clicking_search` ← NEW
16. `after_clicking_search` ← NEW

**Total: 17 screenshots** for complete flow debugging!

## Error Handling

New error scenarios covered:

- **Input field not found**: Screenshot `docket_input_not_found.png`
- **Search button not found**: Screenshot `search_button_not_found.png`
- **Docket search error**: Screenshot `docket_search_error.png`

## Code Quality

### Robustness Features:
- ✅ 6 different selectors for input field
- ✅ 8 different selectors for search button
- ✅ 3-second wait for page load
- ✅ 15-second timeout for finding elements
- ✅ Clear field before entering text
- ✅ 4 new screenshots for debugging
- ✅ Comprehensive error handling
- ✅ Detailed logging

## Next Steps

After testing succeeds with the standalone script, update the chatbot to add a fourth phase that:

1. Shows a text input field for docket number
2. Gets user input
3. Executes Phase 4: Enter docket number and click search

## Summary

✅ **Docket number parameter added** to `select_docket()`
✅ **Input field search** with 6 selectors
✅ **Search button click** with 8 selectors
✅ **Test updated** to test full flow with docket number
✅ **4 new screenshots** for docket number entry and search
✅ **Error handling** for input field and search button
✅ **Ready to test** with `python app/test_docket_selection.py`

The automation now supports the complete four-level hierarchy: **State → District → Docket Number → Search**! 🚀
