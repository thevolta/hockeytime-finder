# Step 6 — Production cache + 6-hour refresh

This changes HockeyTime Finder from "scrape on page load" to a cached
production architecture.

## Replace / add

Replace:
- `app/main.py`
- `app/api/routes.py`
- `app/static/app.js`
- `requirements.txt`
- `.gitignore`

Add:
- `app/services/event_cache.py`
- `app/services/refresh_service.py`
- `app/services/scheduler_service.py`

## How it works

### Visitors

Browser -> `/api/events` -> SQLite cache

No rink websites or APIs are contacted when users load the site.

### Automatic refresh

Every 6 hours:

Provider sources -> normalized events -> SQLite cache

### Failure behavior

Each rink/source is replaced independently.

If AZ Ice, Mullett, or Ice Den temporarily fails, HockeyTime Finder keeps that
rink's previous successful cached events instead of deleting them.

### Manual refresh

The existing Refresh button now calls:

POST `/api/refresh`

The refresh runs in the background. The button polls `/api/status` until it is
finished.

A 5-minute manual cooldown prevents repeated public refresh requests from
hammering the source websites.

## First local run

Install the new dependency:

```powershell
pip install -r requirements.txt
```

Then restart Uvicorn:

```powershell
uvicorn app.main:app --reload
```

The first startup with an empty database launches an immediate background
refresh. You can watch it with:

http://127.0.0.1:8000/api/status

## Production note

This in-process scheduler is ideal while HockeyTime Finder is deployed as a
single FastAPI instance/worker.

If you later scale to multiple application workers or multiple servers, move the
6-hour refresh to one external scheduled job (Render Cron, GitHub Actions,
Railway cron, etc.) so only one scheduler performs refreshes.

Suggested commit:

`Add production calendar cache and scheduled refresh`
