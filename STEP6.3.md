# Step 6.3 — Ice Den Mindbody registration links

## Replace

- `app/providers/rss_provider.py`
- `app/config/sources.yaml`

## Change

Ice Den schedules still come from the existing RSS feeds.

The user-facing Register / View links now use:

### Ice Den Scottsdale

https://clients.mindbodyonline.com/classic/ws?studioid=760588&stype=-103&sView=day&sLoc=0

### Ice Den Chandler

https://clients.mindbodyonline.com/classic/ws?studioid=884177&stype=-103&sTG=28&sView=week&sLoc=1&sTrn=100000014

The original SportsEngine event page remains stored as `source_url`.

## Important

Because production now serves events from SQLite cache, replacing these files
does not immediately change already-cached events.

After Uvicorn reloads, click the HockeyTime Finder Refresh button once, or:

POST /api/refresh

Then new cached Ice Den events will contain the Mindbody registration URLs.

Suggested commit:

`Use Mindbody registration links for Ice Den`
