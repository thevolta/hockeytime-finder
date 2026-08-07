# Step 4 — Web UI

This patch adds the first usable HockeyTime Finder frontend directly to the
existing FastAPI application.

## Files

Replace:

- `app/main.py`

Add:

- `app/static/index.html`
- `app/static/styles.css`
- `app/static/app.js`

## Run

Activate the virtual environment and start the API:

```powershell
.\.venv\Scripts\Activate
uvicorn app.main:app --reload
```

Then open:

http://127.0.0.1:8000

The root URL now displays the HockeyTime Finder calendar instead of JSON.

API documentation remains available at:

http://127.0.0.1:8000/docs

## Included

- Week calendar
- Month calendar
- Upcoming/list calendar
- Event type filters
- Rink filter
- Upcoming-event cards
- Event detail dialog
- Register/View button
- Per-event ICS download
- Full combined `/calendar.ics` subscription link
- Mobile responsive layout

The UI reads directly from `/api/events`, so provider improvements automatically
appear in the calendar without changing the frontend.
