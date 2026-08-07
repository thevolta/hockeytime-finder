# Step 5.1 — Prevent one provider from blocking the whole site

## Replace

- `app/services/source_loader.py`
- `app/api/routes.py`

## Why

Previously `/api/events` fetched every source sequentially. If Mullett or DaySmart
was slow, the frontend stayed on "Loading schedules…" and even the healthy
Ice Den RSS feeds never appeared.

This patch:

- fetches providers concurrently
- returns healthy sources even when another source errors
- pre-filters providers for `?rink=...`
- adds `/api/status` for quick troubleshooting

## Test

With Uvicorn running, replace the files and wait for auto-reload.

Open this first:

http://127.0.0.1:8000/api/events?rink=Ice%20Den%20Chandler

It should return quickly.

Then:

http://127.0.0.1:8000/api/events?rink=AZ%20Ice%20Arcadia

Then:

http://127.0.0.1:8000/api/status

Finally refresh:

http://127.0.0.1:8000

If one provider fails, the UI should still show events from the others.

Suggested commit:

`Prevent slow providers from blocking event feed`
