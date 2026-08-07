# Step 5.4 — Consolidated provider stabilization

This patch addresses all issues found during Step 5.3 testing.

## Replace

- `app/providers/rss_provider.py`
- `app/providers/daysmart_provider.py`
- `app/providers/sportified_provider.py`
- `app/services/source_loader.py`
- `app/config/sources.yaml`

## Fixes

### Ice Den
- RSS is now downloaded with `requests` and an explicit 8-second timeout.
- Duplicate feed entries are removed.
- Chandler/Scottsdale can return even when another provider is unhealthy.

### AZ Ice / DaySmart
- Handles DaySmart fields that sometimes arrive as JSON objects instead of text.
- Peoria and Arcadia share one company-wide in-memory payload.
- Live window reduced to 14 days until database/background refresh is added.
- Uses smaller 2-day chunks with concurrent requests.
- Preserves capacity, registered-count and open-slot fields.

### Mullett
- Uses the public hockey pages rather than the blocked `/schedule` page.
- Prefers actual table rows.
- Suppresses combined parent-div duplicate events.
- De-dupes using event type + start/end time.
- Keeps product registration links.

## Test order

1. `/api/events?rink=Ice%20Den%20Chandler`
2. `/api/events?rink=Ice%20Den%20Scottsdale`
3. `/api/events?rink=Mullett`
4. `/api/events?rink=AZ%20Ice%20Arcadia`
5. `/api/events?rink=AZ%20Ice%20Peoria`
6. `/api/status`
7. `/`

Suggested commit:

`Stabilize all hockey event providers`
