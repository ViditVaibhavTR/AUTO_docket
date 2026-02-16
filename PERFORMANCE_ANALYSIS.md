# Performance Analysis - Auto Docket Automation

## Executive Summary
**Total Time:** 5 minutes (295 seconds)
**Target Time:** < 2 minutes (< 120 seconds)
**Time Savings Potential:** 60-70% (175+ seconds)

## Timing Breakdown by Phase

| Phase | Duration | time.sleep() | WebDriverWait Delays | % of Total |
|-------|----------|--------------|---------------------|-----------|
| Browser Start | 17s | ~5s | ~12s | 6% |
| Gateway Config | 15s | 0s | ~15s | 5% |
| IAC Config | 21s | ~1s | ~20s | 7% |
| **WestLaw Login** | **53s** | ~4s | **~49s** | **18%** |
| **Docket Selection** | **68s** | ~11s | **~57s** | **23%** |
| District Selection | 14s | ~2.5s | ~11.5s | 5% |
| Docket Search | 27s | ~3s | ~24s | 9% |
| **Alert Creation** | **80s** | **~30s** | **~50s** | **27%** |

**Top 3 Bottlenecks:**
1. **Alert Creation: 80 seconds** (27% of total time)
2. **Docket Selection: 68 seconds** (23% of total time)
3. **WestLaw Login: 53 seconds** (18% of total time)

---

## Critical Issues Identified

### 🔴 Issue #1: Excessive WebDriverWait Timeouts (175+ seconds wasted)

**Problem:** WebDriverWait set to 10-15 seconds, but elements often hit max timeout.

**Evidence:**
- `alert_routes.py` line 57: `wait = WebDriverWait(driver, 10)` - used 15+ times
- `westlaw_login.py` line 42: `wait = WebDriverWait(driver, 5)` - hitting timeout
- `docket_selection.py` lines 84, 138, 206, etc: Multiple 2-15 second waits

**Impact:** Each failed selector attempt waits full timeout duration. With multiple selector attempts per step, this adds up to ~175 seconds of wasted waiting.

**Solution:** Reduce all WebDriverWait timeouts to 2-3 seconds for faster failure detection.

---

### 🔴 Issue #2: Not Using Smart Waits (30+ seconds wasted)

**Problem:** Files use `time.sleep()` extensively instead of event-driven `SmartWaits`.

**Evidence:**
- `alert_routes.py` has **~30 seconds** of `time.sleep()` calls:
  - Line 58: `time.sleep(3)` - before notification icon
  - Line 80: `time.sleep(2)` - after clicking notification
  - Line 102: `time.sleep(3)` - after create alert
  - Line 156: `time.sleep(2)` - start of setup
  - Line 180: `time.sleep(3)` - after basics
  - Line 194: `time.sleep(3)` - after content
  - Line 208: `time.sleep(3)` - after search terms
  - Line 224: `time.sleep(2)` - after email
  - Line 231: `time.sleep(3)` - after delivery
  - Line 267: `time.sleep(3)` - after save

**Impact:** Fixed delays when page may be ready sooner. Estimated 15-20 seconds of unnecessary waiting.

**Solution:** Replace with `SmartWaits.wait_for_page_ready()` and element-specific waits.

---

### 🔴 Issue #3: Popup Blocker Running Too Slowly

**Problem:** Background popup blocker removes overlays AFTER automation attempts interaction.

**Evidence from logs:**
```
2026-02-12 15:26:06 | INFO | remove_blocking_overlays - ✓ Removed 20 blocking overlay(s)
2026-02-12 15:26:42 | INFO | remove_blocking_overlays - ✓ Removed 22 blocking overlay(s)
2026-02-12 15:27:16 | INFO | remove_blocking_overlays - ✓ Removed 27 blocking overlay(s)
2026-02-12 15:27:54 | INFO | remove_blocking_overlays - ✓ Removed 37 blocking overlay(s)
```

**Impact:**
- Automation attempts to click elements
- Elements are blocked by overlays
- Click fails or hits wrong element
- WebDriverWait times out
- Popup blocker eventually removes overlays
- Retry succeeds but time is wasted

**Solution:** Proactively call `popup_blocker.remove_blocking_overlays()` BEFORE each major interaction.

---

### 🟡 Issue #4: Inefficient Selector Ordering

**Problem:** Working selectors are not always first in the list, causing unnecessary timeout delays.

**Evidence:**
- `alert_routes.py` line 61-64: Two selectors, but no guarantee first works
- Multiple files iterate through 5-10 selectors, each with 2-15 second timeout

**Impact:** If working selector is 5th in list, automation waits through 4 failed attempts first (40-60 seconds wasted per element).

**Solution:** Reorder selectors based on success rate from logs - put known working selectors FIRST.

---

### 🟡 Issue #5: Smart Waits Not Actually Used

**Problem:** `smart_waits.py` exists but is barely used in the codebase.

**Evidence:**
- `docket_selection.py` imports SmartWaits but never calls it
- `alert_routes.py` doesn't import SmartWaits at all
- `westlaw_login.py` imports SmartWaits but never uses it

**Impact:** All the optimization work on smart_waits is wasted - code still uses slow time.sleep().

**Solution:** Replace all `time.sleep()` and basic `WebDriverWait` with `SmartWaits` methods.

---

## Detailed Recommendations

### Priority 1: Optimize Alert Creation (Save ~50 seconds)

**Current: 80 seconds → Target: 25-30 seconds**

Changes to `app/api/alert_routes.py`:

1. **Reduce WebDriverWait timeout**
   ```python
   # Line 57: Change from 10 to 3 seconds
   wait = WebDriverWait(driver, 3)
   ```

2. **Replace time.sleep() with smart waits**
   ```python
   # Line 58: Replace time.sleep(3) with:
   SmartWaits.wait_for_page_ready(driver, timeout=5)

   # Line 80: Replace time.sleep(2) with:
   SmartWaits.wait_for_ajax_complete(driver, timeout=2)

   # Similar replacements for lines 102, 156, 180, 194, 208, 224, 231, 267
   ```

3. **Add proactive overlay removal**
   ```python
   # Before line 79 (clicking notification icon):
   from src.utils.popup_blocker import PopupBlocker
   PopupBlocker.remove_blocking_overlays(driver)
   notification_icon.click()
   ```

### Priority 2: Optimize Docket Selection (Save ~40 seconds)

**Current: 68 seconds → Target: 20-25 seconds**

Changes to `app/src/automation/docket_selection.py`:

1. **Reduce selector iteration timeouts**
   ```python
   # Line 84: Change from 2 to 1 second
   short_wait = WebDriverWait(driver, 1)
   ```

2. **Add overlay removal before clicks**
   ```python
   # Before line 98 (clicking content types):
   PopupBlocker.remove_blocking_overlays(driver)
   driver.execute_script("arguments[0].click();", content_types_element)
   ```

3. **Replace time.sleep() with smart waits**
   ```python
   # Line 58: Replace time.sleep(1) with:
   SmartWaits.wait_for_page_ready(driver, timeout=3)
   ```

### Priority 3: Optimize WestLaw Login (Save ~30 seconds)

**Current: 53 seconds → Target: 15-20 seconds**

Changes to `app/src/automation/westlaw_login.py`:

1. **Use SmartWaits instead of time.sleep()**
   ```python
   # Line 131: Replace time.sleep(1) with:
   SmartWaits.wait_for_page_ready(driver, timeout=3)

   # Line 236: Replace time.sleep(1) with:
   SmartWaits.wait_for_page_ready(driver, timeout=3)
   ```

2. **Reduce field entry delays**
   ```python
   # Lines 169-196: Reduce all time.sleep() by 50%
   time.sleep(0.05)  # was 0.1
   time.sleep(0.15)  # was 0.3
   ```

### Priority 4: Optimize District Selection & Docket Search (Save ~25 seconds)

**Current: 41 seconds → Target: 10-15 seconds**

Changes to `app/api/docket_routes.py`:

1. **Reduce WebDriverWait timeouts**
   ```python
   # Line 126: Change from 15 to 3 seconds
   wait = WebDriverWait(driver, 3)

   # Line 219: Change from 5 to 2 seconds
   wait = WebDriverWait(driver, 2)
   ```

2. **Replace time.sleep() with smart waits**
   ```python
   # Line 165: Replace time.sleep(0.5)
   SmartWaits.wait_for_element_stable(driver, district_element)

   # Line 168: Replace time.sleep(2)
   SmartWaits.wait_for_page_ready(driver, timeout=3)
   ```

3. **Add overlay removal**
   ```python
   # Before line 166 (clicking district):
   PopupBlocker.remove_blocking_overlays(driver)
   driver.execute_script("arguments[0].click();", district_element)
   ```

---

## Expected Results After Optimization

| Phase | Before | After | Savings |
|-------|--------|-------|---------|
| Browser Start | 17s | 12s | 5s |
| Gateway Config | 15s | 8s | 7s |
| IAC Config | 21s | 12s | 9s |
| WestLaw Login | 53s | 20s | **33s** |
| Docket Selection | 68s | 25s | **43s** |
| District Selection | 14s | 8s | 6s |
| Docket Search | 27s | 12s | 15s |
| Alert Creation | 80s | 30s | **50s** |
| **Total** | **295s** | **~127s** | **~168s (57%)** |

**New Total Time: ~2 minutes (127 seconds)**

---

## Implementation Priority

1. ✅ **Quick Win (30 min):** Reduce all WebDriverWait timeouts from 10-15s to 2-3s
2. ✅ **Medium Impact (1 hour):** Replace time.sleep() in alert_routes.py with SmartWaits
3. ✅ **High Impact (1 hour):** Add proactive PopupBlocker.remove_blocking_overlays() before all clicks
4. ✅ **Long Term (2 hours):** Replace all time.sleep() across all files with SmartWaits

---

## Files to Modify (in priority order)

1. `app/api/alert_routes.py` - 80s → 30s (save 50s)
2. `app/src/automation/docket_selection.py` - 68s → 25s (save 43s)
3. `app/src/automation/westlaw_login.py` - 53s → 20s (save 33s)
4. `app/api/docket_routes.py` (district + search) - 41s → 20s (save 21s)
5. `app/src/automation/iac_config.py` - 21s → 12s (save 9s)
6. `app/src/automation/gateway_config.py` - 15s → 8s (save 7s)
