# Step 5.2 — Fix hanging /api/events

The prior timeout implementation used `as_completed()`. That function only
returns futures after they finish, so the API could still wait forever before
the timeout check ran.

This patch:

- enforces a real 15-second wall-clock provider budget
- returns completed providers even if another provider is still slow
- prevents a slow Mullett/DaySmart source from blanking the entire website
- adds final event deduplication
- deduplicates repeated SportsEngine/Ice Den RSS entries

## Replace

- `app/services/source_loader.py`
- `app/providers/rss_provider.py`

## Test

After Uvicorn reloads:

1. http://127.0.0.1:8000/api/events?rink=Ice%20Den%20Chandler
2. http://127.0.0.1:8000/api/events?rink=AZ%20Ice%20Arcadia
3. http://127.0.0.1:8000/api/events
4. http://127.0.0.1:8000

The unfiltered `/api/events` request should return within about 15 seconds even
if one provider is unhealthy. The response `errors` array will identify any
provider that exceeded the response budget.

Suggested commit:
`Fix provider timeout and duplicate events`
