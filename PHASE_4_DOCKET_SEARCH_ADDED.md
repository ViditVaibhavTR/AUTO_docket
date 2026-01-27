# Phase 4: Docket Number Search Added to Streamlit ✅

## Summary

Added **Phase 4** to the Streamlit chatbot frontend where users can:
1. Enter a docket number in a text input field
2. Click "Search Docket" button
3. Backend fills the number in the correct field and searches
4. This is a **separate phase** (not clubbed with Phase 3)

## Complete Four-Phase Flow

```
Phase 1: Content Types → Dockets
    ↓
Phase 2: Dockets by State → California
    ↓
Phase 3: District Selection → Southern District
    ↓
Phase 4: Docket Number Input → Search ← NEW!
    ↓
Results
```

## Changes Made

### 1. New Session State Variables

**File**: [chatbot.py](app/chatbot.py:243-249)

```python
# Phase 4: Docket number input
if 'show_docket_number_input' not in st.session_state:
    st.session_state.show_docket_number_input = False
if 'docket_number' not in st.session_state:
    st.session_state.docket_number = None
if 'docket_search_running' not in st.session_state:
    st.session_state.docket_search_running = False
```

### 2. Updated Phase 3 Completion

**File**: [chatbot.py](app/chatbot.py:671-674)

**Before**: Phase 3 marked as completed and showed final screen
```python
st.session_state.district_running = False
st.session_state.completed = True
st.rerun()
```

**After**: Phase 3 transitions to Phase 4 UI
```python
st.session_state.district_running = False
st.session_state.show_docket_number_input = True  # NEW: Show Phase 4 UI
st.rerun()
```

### 3. Phase 4 UI - Docket Number Input

**File**: [chatbot.py](app/chatbot.py:676-713)

Shows:
- Current state and district selected
- Text input field with placeholder "e.g., 1:25-CV-01815"
- Submit button "🔍 Search Docket" (disabled until text is entered)
- Back button to return to district selection

```python
# Docket number input field
docket_number_input = st.text_input(
    "Docket Number",
    placeholder="e.g., 1:25-CV-01815",
    key="docket_number_input_field",
    help="Enter the docket number in the format: X:YY-CV-NNNNN"
)

# Submit button
if st.button("🔍 Search Docket", disabled=not docket_number_input):
    st.session_state.docket_number = docket_number_input
    st.session_state.show_docket_number_input = False
    st.session_state.docket_search_running = True
    st.rerun()
```

### 4. Phase 4 Execution - Docket Search

**File**: [chatbot.py](app/chatbot.py:715-861)

Executes the backend search:

1. **Find docket number input field** using optimized selectors:
   - `By.ID, "co_search_advancedSearch_DN"` (FASTEST - <1s)
   - `By.NAME, "co_search_advancedSearch_DN"`
   - `By.XPATH, '//label[contains(text(), "Docket Number")]/..//input'`

2. **Enter docket number**:
   ```python
   input_element.clear()
   input_element.send_keys(st.session_state.docket_number)
   ```

3. **Find search button** using optimized selectors:
   - `By.ID, "searchButton"` (FASTEST - <1s)
   - `By.XPATH, '//button[@id="searchButton"]'`
   - With KNOS avoidance built-in

4. **Click search button**:
   ```python
   search_button.click()  # or JavaScript click as fallback
   ```

5. **Take screenshots** at each step for debugging

### 5. Updated Login Prompt Condition

**File**: [chatbot.py](app/chatbot.py:306)

Added exclusions for Phase 4 states:
```python
and not st.session_state.get('show_docket_number_input', False)
and not st.session_state.get('docket_search_running', False)
```

### 6. Updated Completion Screen

**File**: [chatbot.py](app/chatbot.py:872-874)

Shows docket number and search status:
```python
if st.session_state.docket_number:
    st.markdown(f"**Docket Number:** {st.session_state.docket_number}")
    st.markdown(f"**Search Status:** ✅ Completed")
```

## Features

### ✅ Optimized Performance
- Uses fastest selectors first (Direct ID)
- 5-second timeout for quick fallback
- Minimized sleep delays
- Expected execution time: **~4 seconds** for Phase 4

### ✅ Separate Phase Execution
- Phase 3 completes → Shows Phase 4 UI
- User enters docket number → Phase 4 executes
- Not clubbed together

### ✅ User Experience
- Clear input field with placeholder
- Submit button disabled until text entered
- Back button to modify district selection
- Progress indicators during execution

### ✅ Error Handling
- Screenshots at critical points
- Error messages displayed to user
- Fallback selectors if primary fails

### ✅ KNOS Avoidance
- All selectors exclude KNOS buttons
- Explicit KNOS filtering in search button detection

## Testing

To test the complete flow:

1. Start the chatbot:
   ```bash
   streamlit run app/chatbot.py
   ```

2. Complete phases:
   - **Phase 1**: Click "Yes, Select Docket" → Navigates to Dockets
   - **Phase 2**: Click a state (e.g., "California")
   - **Phase 3**: Click a district (e.g., "Southern District")
   - **Phase 4**: Enter docket number (e.g., "1:25-CV-01815") → Click "Search Docket"

3. Verify:
   - ✅ Docket number entered in correct field (`co_search_advancedSearch_DN`)
   - ✅ Orange search button clicked (NOT KNOS)
   - ✅ Search executes successfully
   - ✅ Completion screen shows all details

## Flow Diagram

```
User Journey:

1. Login → ✅
2. Select Docket → Click "Yes"
3. Phase 1 executes → Navigate to Dockets → ✅
4. Phase 2 UI → Select California → ✅
5. Phase 2 executes → Click California → ✅
6. Phase 3 UI → Select Southern District → ✅
7. Phase 3 executes → Click Southern District → ✅
8. Phase 4 UI → Enter "1:25-CV-01815" → Click "Search" ← NEW
9. Phase 4 executes → Fill field + Click search → ✅ ← NEW
10. Completion screen → Shows all details → ✅
```

## Screenshots Captured

Phase 4 adds these screenshots:
1. `before_docket_number_input` - Page before entering number
2. `after_entering_docket_number` - Shows number entered
3. `before_searching_for_search_button` - Before button search
4. `before_clicking_search` - Shows which button will be clicked
5. `after_clicking_search` - Search results or error

## Summary

✅ **Phase 4 UI added** - Text input for docket number
✅ **Phase 4 execution added** - Fills field and searches
✅ **Separate phase flow** - Not clubbed with Phase 3
✅ **Optimized performance** - Uses fastest selectors first
✅ **KNOS avoidance** - Built into all selectors
✅ **Error handling** - Screenshots and error messages
✅ **User experience** - Clear flow with back button

The Streamlit chatbot now supports the complete four-phase docket selection and search workflow! 🎉
