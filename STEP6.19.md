# Step 6.19 — Fix 7 Day lock-up

Replace:
- app/static/app.js
- app/static/index.html

Root cause:
The custom `sevenDay` FullCalendar view could recurse / hang when switching views.

Fix:
- Removes the custom FullCalendar view entirely.
- Uses only built-in `timeGridDay` / `listWeek` views.
- Applies a rolling `visibleRange` of today through the next 6 days.
- 7 Day remains the default.
- Selecting Week/Month/Upcoming disables the rolling range and restores normal behavior.
- Selecting 7 Day re-enables the rolling range and jumps back to today.

After copying:
1. Let Uvicorn reload.
2. Hard refresh with Ctrl+Shift+R.
3. Verify:
   - Page opens on 7 Day
   - 7 Day shows today through +6 days
   - Week / Month / Upcoming switch normally
   - Switching back to 7 Day does not hang

Suggested commit:
Fix seven-day view lockup
