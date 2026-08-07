# Step 5 — Direct DaySmart API

This patch replaces the AZ Ice HTML/iframe parser with DaySmart's JSON API.

## Replace

- `app/providers/daysmart_provider.py`
- `app/models/event.py`
- `app/config/sources.yaml`
- `app/static/app.js`

## What changed

- Calls `https://api.daysmartrecreation.com/v1/events`
- Automatically fetches all API pages
- Uses DaySmart's included event summaries/resources/facilities
- Filters AZ Ice by facility:
  - 1 = AZ Ice Peoria
  - 3 = AZ Ice Arcadia
- Includes Stick Time / Sticktime
- Includes Pickup / Open Hockey
- Ignores unrelated sessions like Freestyle and Public Skate
- Pulls registration capacity / registered count / open slots when provided
- Keeps the AZ Ice hockey-program registration page as the registration fallback
- Displays availability metadata in the frontend when DaySmart returns it

## Test

With Uvicorn running (`--reload` should update automatically), open:

http://127.0.0.1:8000/api/diagnostics/daysmart

You want both facilities to say:

```json
"api_fetch_ok": true
```

Then open:

http://127.0.0.1:8000/api/events?rink=AZ%20Ice

and finally:

http://127.0.0.1:8000

AZ Ice Peoria / Arcadia should now appear in the rink filter whenever upcoming
Stick Time or Pickup Hockey events exist in the 30-day window.

## Commit

Suggested commit message:

`Replace AZ Ice scraper with DaySmart API`
