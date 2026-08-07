# Step 6.12 — No Work Hours ignores weekends

Replace:
- app/static/app.js

Behavior:
- Monday-Friday: No work hours hides events overlapping 9:00 AM-4:00 PM Arizona time.
- Saturday-Sunday: No work hours does not hide anything.
- AM/PM filters continue to apply normally on weekends.
- Calendar, matching count, and Next Sessions all use the same filteredEvents() logic.

After copying:
1. Let Uvicorn reload.
2. Hard refresh with Ctrl+Shift+R.

Suggested commit:
Ignore weekends in no-work-hours filter
