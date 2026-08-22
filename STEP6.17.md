# Step 6.17 — Fix rolling 7 Day view

Replace:
- app/static/app.js

Fix:
- 7 Day now uses a concrete `timeGridDay` base view on desktop.
- Mobile uses a concrete `listDay` base view.
- Both are extended to exactly 7 days.
- Selecting `7 Day` explicitly resets the calendar to today.
- The range is therefore always today + the next 6 days instead of the Sunday/Monday calendar week.
- Previous/Next still moves the rolling view by 7 days.

Example:
If today is Saturday Aug 22:
7 Day = Sat Aug 22 through Fri Aug 28.

After copying:
1. Let Uvicorn reload.
2. Hard refresh with Ctrl+Shift+R.
3. Switch to Month or Week, then select 7 Day to verify it jumps back to today.

Suggested commit:
Fix rolling seven-day calendar view
