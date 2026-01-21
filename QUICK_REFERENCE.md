# Quick Reference - Updated Docket Selection Flow

## What Changed?

The chatbot now routes **ALL** navigation to the `DocketSelector` class, which handles the complete automation flow.

## The Complete Flow

```
┌─────────────────────────────────────────────────────────┐
│  User clicks "California" in Streamlit UI               │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  run_docket_selection(                                  │
│    driver,                                              │
│    browser_manager,                                     │
│    category="Dockets by State",                         │
│    specific_docket="California"                         │
│  )                                                      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  DocketSelector.select_docket() handles EVERYTHING:     │
│                                                          │
│  1. Click "Content Types" tab                           │
│     📸 Screenshot: before_clicking_content_types        │
│     📸 Screenshot: after_clicking_content_types         │
│                                                          │
│  2. Click "Dockets" option                              │
│     📸 Screenshot: after_clicking_dockets               │
│                                                          │
│  3. Click "Dockets by State" category                   │
│     📸 Screenshot: after_clicking_category              │
│                                                          │
│  4. Click "California" state                            │
│     📸 Screenshot: after_clicking_specific_docket       │
│                                                          │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  Returns "success" or "error: <message>"                │
└─────────────────────────────────────────────────────────┘
```

## Key Files

1. **[app/chatbot.py](app/chatbot.py)** - Streamlit UI
   - Line 126-169: `run_docket_selection()` function
   - Line 345-369: Where state selection triggers DocketSelector

2. **[app/src/automation/docket_selection.py](app/src/automation/docket_selection.py)** - The automation engine
   - Line 23-209: `DocketSelector.select_docket()` method

3. **[app/test_docket_selection.py](app/test_docket_selection.py)** - Standalone test script
   - Uses same DocketSelector pattern

## What to Test

### Happy Path Test
1. Start Streamlit: `streamlit run app/chatbot.py`
2. Click "Yes, Let's Go!"
3. Wait for login to complete
4. Click "Yes, Select Docket"
5. Click "California" (or any state)
6. Verify it navigates: Content Types → Dockets → Dockets by State → California

### Check Screenshots
- Location: `screenshots/` folder
- Look for the sequence of screenshots showing each step

### Check Logs
- Console output shows detailed step-by-step progress
- Look for the `STARTING DOCKET SELECTION TEST` header
- Should see `✓✓✓ DOCKET SELECTION COMPLETED SUCCESSFULLY ✓✓✓`

## If Issues Occur

1. **Content Types not found**
   - Check screenshot: `content_types_not_found.png`
   - Check debug file: `debug_page_source.html`

2. **Dockets option not found**
   - Check screenshot: `dockets_not_found.png`
   - Check debug file: `debug_page_after_content_types.html`

3. **Category not found**
   - Check screenshot: `category_not_found.png`

4. **State not found**
   - Check screenshot: `specific_docket_not_found.png`

## Benefits of This Approach

✅ **Single Source of Truth** - All navigation logic in DocketSelector
✅ **Automatic Screenshots** - Visual debugging at every step
✅ **Robust Selectors** - Tries multiple XPath patterns per element
✅ **Better Error Messages** - Clear indication of where it failed
✅ **Less Code** - Removed ~150 lines of duplicate code
✅ **Easier Testing** - Can run standalone with test_docket_selection.py

## Testing the Automation Standalone

If you want to test just the docket selection without the full UI:

```bash
cd "c:\Users\C303190\OneDrive - Thomson Reuters Incorporated\Desktop\AUTO DOCKET"
python app/test_docket_selection.py
```

This will:
- Run the full login flow
- Automatically select: Dockets by State → California
- Keep browser open for 10 seconds for verification
- Show detailed logs and screenshots
