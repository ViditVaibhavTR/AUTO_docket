# Two-Phase Flow Implementation ✅

## Overview

The chatbot now executes the automation in **two separate phases** based on user interaction:

### Phase 1: Content Types → Dockets
**Triggered when**: User clicks "Yes, Select Docket"
**Executes immediately**: Navigates to Content Types → Dockets in the background

### Phase 2: Dockets by State → California
**Triggered when**: User clicks "California" (or any state)
**Executes immediately**: Navigates to Dockets by State → California in the background

## Complete User Flow

```
┌─────────────────────────────────────────────────────────┐
│  1. User starts chatbot and clicks "Yes, Let's Go!"    │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  2. Automation runs: Gateway + IAC + WestLaw Login     │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  3. ✅ Login completed successfully!                    │
│     Should we start with docket selection?              │
│                                                          │
│     [✅ Yes, Select Docket]  [❌ No, Exit]              │
└──────────────────┬──────────────────────────────────────┘
                   │ User clicks "Yes, Select Docket"
                   ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 1: Executing in background...                   │
│  🔄 Navigating to Dockets...                            │
│                                                          │
│  ✓ Click "Content Types" tab                            │
│  ✓ Click "Dockets" option                               │
│  ✅ Success!                                             │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  4. 📂 Dockets by State                                 │
│     Please select a state:                              │
│                                                          │
│     [📄 California]                                     │
│     [📄 New York]                                       │
│     [📄 Texas]                                          │
│                                                          │
│     [⬅️ Back]                                           │
└──────────────────┬──────────────────────────────────────┘
                   │ User clicks "California"
                   ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 2: Executing in background...                   │
│  🔄 Selecting state docket...                           │
│                                                          │
│  ✓ Click "Dockets by State"                             │
│  ✓ Click "California"                                   │
│  ✅ Success!                                             │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  5. ✅ Task done                                         │
│     Selected State Docket: California                   │
│                                                          │
│     [🔄 Run Again]  [🚪 Exit]                           │
└─────────────────────────────────────────────────────────┘
```

## Implementation Details

### Phase 1: Content Types → Dockets

**File**: [chatbot.py](app/chatbot.py) lines 316-415

**Triggered by**: `st.session_state.navigate_to_dockets = True`

**What it does**:
1. Shows spinner: "Executing Content Types → Dockets..."
2. Clicks "Content Types" tab using multiple selectors
3. Clicks "Dockets" option using multiple selectors
4. Takes screenshots at each step
5. Sets `dockets_nav_complete = True`
6. Shows state selection UI

**Code**:
```python
elif st.session_state.get('navigate_to_dockets', False) and not st.session_state.get('dockets_nav_complete', False):
    with st.spinner("Executing Content Types → Dockets..."):
        # Click Content Types
        # Click Dockets
        # Mark complete
        st.session_state.dockets_nav_complete = True
        st.session_state.show_docket_categories = True
```

### Phase 2: Dockets by State → California

**File**: [chatbot.py](app/chatbot.py) lines 444-541

**Triggered by**: `st.session_state.docket_running = True`

**What it does**:
1. Shows spinner: "Navigating: Dockets by State → California..."
2. Clicks "Dockets by State" category
3. Waits 3 seconds for page load
4. Tries 5 different selectors to find "California"
5. Scrolls into view
6. Clicks "California"
7. Takes screenshots at each step
8. Marks as completed

**Code**:
```python
elif st.session_state.docket_running and not st.session_state.completed:
    with st.spinner(f"Navigating: Dockets by State → {st.session_state.selected_docket}..."):
        # Click "Dockets by State"
        # Wait 3 seconds
        # Try 5 selectors for state
        # Scroll into view
        # Click state
        result = "success"
```

## Key Features

### ✅ Two-Phase Separation
- **Phase 1**: Happens when user confirms docket selection
- **Phase 2**: Happens when user selects specific state
- User sees progress for each phase separately

### ✅ Multiple Selectors
Both phases use multiple XPath selectors for robustness:
- **Content Types**: 3 selectors
- **Dockets**: 4 selectors
- **State (California)**: 5 selectors

### ✅ Screenshots at Every Step
- `before_content_types_click`
- `before_clicking_content_types`
- `after_clicking_content_types`
- `before_clicking_dockets`
- `after_clicking_dockets`
- `before_clicking_dockets_by_state`
- `after_clicking_dockets_by_state`
- `before_searching_state`
- `before_clicking_state`
- `after_clicking_state`

### ✅ Error Handling
Each phase has try-catch blocks with:
- Error screenshots
- Detailed logging
- Graceful failure with cleanup

### ✅ Progress Indicators
- Phase 1: "🔄 Navigating to Dockets..."
- Phase 2: "🔄 Selecting state docket..."

## Session State Variables

### New Variables Added:
- `navigate_to_dockets`: Boolean to trigger Phase 1
- `dockets_nav_complete`: Boolean to mark Phase 1 completion

### Existing Variables Used:
- `docket_running`: Boolean to trigger Phase 2
- `selected_docket`: Stores the selected state name
- `show_docket_categories`: Shows state selection UI

## Code Locations

### Session State Initialization
**Lines 231-234**: Initialize new flags
```python
if 'navigate_to_dockets' not in st.session_state:
    st.session_state.navigate_to_dockets = False
if 'dockets_nav_complete' not in st.session_state:
    st.session_state.dockets_nav_complete = False
```

### Phase 1 Trigger
**Lines 300-305**: Button click triggers Phase 1
```python
if st.button("✅ Yes, Select Docket", ...):
    st.session_state.navigate_to_dockets = True
    st.rerun()
```

### Phase 1 Execution
**Lines 316-415**: Content Types → Dockets automation

### Phase 2 Trigger
**Lines 430-436**: State button click triggers Phase 2
```python
if st.button(f"📄 {state}", ...):
    st.session_state.selected_docket = state
    st.session_state.docket_running = True
    st.rerun()
```

### Phase 2 Execution
**Lines 444-541**: Dockets by State → California automation

### Cleanup on Restart
**Lines 576-577**: Reset new flags
```python
st.session_state.navigate_to_dockets = False
st.session_state.dockets_nav_complete = False
```

## Benefits of Two-Phase Flow

### 1. **Better User Experience**
- User sees exactly what's happening at each step
- Clear separation between navigation phases
- Progress indicators for each phase

### 2. **Easier Debugging**
- Can identify which phase failed
- Screenshots for each phase separately
- Isolated error handling

### 3. **More Control**
- User explicitly triggers each phase
- Can stop between phases if needed
- Clear decision points

### 4. **Cleaner Code**
- Each phase has its own code block
- No mixing of concerns
- Easier to maintain and update

## Testing the Two-Phase Flow

### Step-by-Step Test

1. **Start chatbot**:
   ```bash
   streamlit run app/chatbot.py
   ```

2. **Click "Yes, Let's Go!"**
   - Watch login automation complete

3. **Click "Yes, Select Docket"**
   - **PHASE 1 EXECUTES**
   - See: "🔄 Navigating to Dockets..."
   - Watch: Content Types → Dockets
   - Result: "✅ Successfully navigated to Content Types → Dockets!"

4. **Click "California"**
   - **PHASE 2 EXECUTES**
   - See: "🔄 Selecting state docket..."
   - Watch: Dockets by State → California
   - Result: "✅ Task done"

### Expected Logs

#### Phase 1 Logs:
```
🔵 User clicked 'Yes, Select Docket' button
Looking for 'Content types' tab...
✓ Found Content Types with: //*[@id="tab3"]
✓ Clicked Content Types tab
Looking for 'Dockets' option...
✓ Found Dockets with: //span[contains(text(), "Dockets")]
✓ Clicked Dockets option
✅ Successfully navigated to Dockets section
```

#### Phase 2 Logs:
```
🟢 PHASE 2: Selecting California
Looking for 'Dockets by State' category...
✓ Found 'Dockets by State'
✓ Clicked 'Dockets by State'
Looking for state: California
Trying state selector: //a[text()="California"]
✓ Found state with: //a[text()="California"]
✓ Found state: California
✓ Clicked state: California
✅ State selection completed successfully!
```

## Comparison: Old vs New Flow

### Old Flow (Single Phase)
```
Click "California"
  ↓
Execute ALL at once:
  - Content Types
  - Dockets
  - Dockets by State
  - California
  ↓
Result shown
```
**Problem**: User doesn't see intermediate progress, harder to debug

### New Flow (Two Phases)
```
Click "Yes, Select Docket"
  ↓
PHASE 1 executes:
  - Content Types
  - Dockets
  ✅ Success shown
  ↓
User sees state list
  ↓
Click "California"
  ↓
PHASE 2 executes:
  - Dockets by State
  - California
  ✅ Success shown
```
**Benefit**: Clear progress, better UX, easier debugging

## Summary

✅ **Two-phase flow implemented**
✅ **Phase 1**: Content Types → Dockets (triggered by "Yes, Select Docket")
✅ **Phase 2**: Dockets by State → California (triggered by state selection)
✅ **Multiple selectors** for robustness
✅ **Screenshots** at every step
✅ **Error handling** for each phase
✅ **Progress indicators** for user feedback

The chatbot now provides a **smoother, more transparent user experience** with clear separation between navigation phases! 🎉
