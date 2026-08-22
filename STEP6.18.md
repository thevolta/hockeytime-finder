# Step 6.18 — Force 7 Day as the default view

Replace:
- app/static/index.html
- app/static/app.js

Fixes:
- 7 Day is explicitly selected in the dropdown markup.
- On every fresh page load, FullCalendar is forced to:
  - go to today
  - switch to sevenDay
- This prevents stale browser/calendar state from opening Week or Month first.

After copying:
1. Let Uvicorn reload.
2. Hard refresh with Ctrl+Shift+R.
3. Close and reopen the page to verify it always starts on 7 Day.

Suggested commit:
Force rolling seven-day view as default
