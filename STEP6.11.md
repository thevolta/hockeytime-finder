# Step 6.11 — AM / PM + No Work Hours filters

Replace:
- app/static/index.html
- app/static/app.js
- app/static/styles.css

New filter group:
- AM
- PM
- No work hours

Behavior:
- AM and PM are both enabled by default.
- Disable PM to show only events that START before 12:00 PM Arizona time.
- Disable AM to show only events that START at 12:00 PM or later Arizona time.
- If both AM and PM are unchecked, no events are shown.
- "No work hours" removes any event overlapping 9:00 AM–4:00 PM Arizona time.

IMPORTANT:
All of these filters use the shared filteredEvents() function, so they affect:
- Calendar
- Matching event count
- Next Sessions / Quick View

After copying:
1. Let Uvicorn reload.
2. Hard refresh with Ctrl+Shift+R.

Suggested commit:
Add AM PM filters to calendar and next sessions
