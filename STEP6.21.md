# Step 6.21 — Remove 7 Day and make Week start today

Replace:
- app/static/index.html
- app/static/app.js

Changes:
- Removes the 7 Day option completely.
- Week is now the default view.
- Week starts on the current day instead of Sunday/Monday.
- Example: if today is Saturday, Week shows Saturday through Friday.
- Previous / Next use FullCalendar's normal weekly navigation.
- Month and Upcoming remain normal built-in views.
- Mobile uses listWeek but still starts from the current day.

After copying:
1. Let Uvicorn reload.
2. Hard refresh with Ctrl+Shift+R.

Suggested commit:
Make week view start on current day
