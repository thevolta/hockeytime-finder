# Step 6.10 — Mobile day colors + No Work Hours

Replace:
- app/static/index.html
- app/static/app.js
- app/static/styles.css

Changes:
- Upcoming/mobile day headings are now dark maroon with cream text.
- The current day is dark green with cream text in Week, Month, and Upcoming views.
- Adds a "No work hours" checkbox.
- When enabled, events overlapping 9:00 AM through 4:00 PM Arizona time are hidden.
- The filter applies to the calendar, matching event count, and Quick View.

After copying:
1. Let Uvicorn reload.
2. Hard refresh with Ctrl+Shift+R.
3. On mobile, reload the page completely if Safari/Chrome has cached the CSS.

Suggested commit:
Fix mobile day colors and add work-hours filter
