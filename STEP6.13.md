# Step 6.13 — Adult Skills category

Replace:
- app/providers/daysmart_provider.py
- app/static/index.html
- app/static/app.js
- app/static/styles.css

Adds:
- Adult Skills as a fourth filter/category.
- DaySmart team 14006 is treated as Adult Skills.
- DaySmart team 12809 is treated as Adult Skills.
- Facility is determined automatically from the DaySmart event, so Gilbert/Peoria
  are assigned by the event resource rather than hard-coded.
- Register/View goes directly to the matching team page.
- Details popup explicitly shows `Registered: X` when DaySmart provides it.
- Registered count falls back to the home-team roster fields when the event
  summary does not contain a count.

Registration pages:
- https://apps.daysmartrecreation.com/dash/x/azice/teams/14006
- https://apps.daysmartrecreation.com/dash/x/azice/teams/12809

IMPORTANT:
The production app reads from SQLite cache, so after replacing these files:
1. Let Uvicorn reload.
2. Click Refresh once.
3. Wait for /api/status to show `"refreshing": false`.
4. Hard refresh the browser.

Suggested commit:
Add Adult Skills DaySmart events
