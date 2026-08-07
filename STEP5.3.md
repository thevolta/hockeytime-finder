# Step 5.3 — Faster DaySmart + Mullett page fallback

## Replace

- `app/providers/daysmart_provider.py`
- `app/providers/sportified_provider.py`
- `app/config/sources.yaml`

## DaySmart changes

- requests only `summary,resource.facility`
- splits the 30-day window into 3-day chunks
- fetches chunks concurrently
- keeps Peoria and Arcadia facility filtering
- preserves capacity/open-slot metadata

## Mullett changes

The filtered `/schedule` endpoint currently responds with HTTP 403 to
server-side requests. This patch instead uses the three public hockey pages:

- /pages/hockey/sticktime
- /pages/hockey/adult-open-hockey
- /pages/hockey/flow-hockey

Those pages contain the visible event tables and registration links.

## Test

1. http://127.0.0.1:8000/api/events?rink=AZ%20Ice%20Arcadia
2. http://127.0.0.1:8000/api/events?rink=AZ%20Ice%20Peoria
3. http://127.0.0.1:8000/api/events?rink=Mullett
4. http://127.0.0.1:8000/api/status
5. http://127.0.0.1:8000

Suggested commit:

`Optimize DaySmart and replace blocked Mullett schedule`
