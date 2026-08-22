# Step 6.20 — Stable 7 Day view

Replace:
- app/static/app.js
- app/static/index.html

This completely removes the custom/visibleRange 7-day logic.

How 7 Day works now:
- Uses FullCalendar's built-in `timeGridWeek` on desktop.
- Uses built-in `listWeek` on mobile.
- Sets `firstDay` to today's weekday.
- If today is Saturday, the range is Saturday -> Friday.
- If today is Wednesday, the range is Wednesday -> Tuesday.
- Prev/Next are FullCalendar's normal week navigation, so they work reliably.
- Selecting Week resets to a normal Sunday-start week.
- Month and Upcoming remain standard built-in views.
- 7 Day is the default on page load.

Why this is more stable:
There are no custom views, no `visibleRange`, no `dateIncrement`, and no
FullCalendar option swapping that can recurse or lock the calendar.

After copying:
1. Let Uvicorn reload.
2. Hard refresh with Ctrl+Shift+R.
3. Verify:
   - Page opens on 7 Day
   - Prev / Next work
   - Week / Month / Upcoming all switch
   - Switching back to 7 Day works repeatedly

Suggested commit:
Use stable built-in rolling seven-day view
