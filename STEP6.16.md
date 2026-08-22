# Step 6.16 — Rolling 7 Day calendar view

Replace:
- app/static/index.html
- app/static/app.js

Adds:
- New `7 Day` view.
- `7 Day` is now the default calendar view.
- It starts on the current day instead of snapping to Sunday/Monday.
- It shows exactly the current day plus the next 6 days.
- Previous/Next moves backward/forward by 7 days.
- The existing Week view remains available if you want the traditional calendar week.
- On mobile, the same 7-day range automatically uses FullCalendar's list layout so seven columns are not squeezed onto the screen.

Example:
If today is Thursday, August 6:
7 Day = Thu Aug 6 through Wed Aug 12

After copying:
1. Let Uvicorn reload.
2. Hard refresh with Ctrl+Shift+R.

Suggested commit:
Add rolling seven-day default view
