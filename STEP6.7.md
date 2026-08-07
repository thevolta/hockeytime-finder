# Step 6.7 — Finalized dark maroon theme + Ice Den links + AZ Ice Gilbert

## Replace

- `app/static/index.html`
- `app/static/styles.css`
- `app/static/app.js`
- `app/providers/rss_provider.py`
- `app/config/sources.yaml`

## Visual updates

- No Coyotes logo
- More dark maroon throughout the UI
- Kachina-inspired maroon / cream / green band across the top
- Fully dark week/month calendar backgrounds
- Maroon weekday headers
- Green current-day highlight
- Dark event colors:
  - Stick Time = forest green
  - Open Hockey = purple
  - Flow Hockey = dark maroon

## Ice Den registration links

Ice Den Chandler:
https://clients.mindbodyonline.com/classic/ws?studioid=884177&stype=-103&sTG=28&sView=week&sLoc=1&sTrn=100000014

Ice Den Scottsdale:
https://clients.mindbodyonline.com/classic/ws?studioid=760588&stype=-103&sView=day&sLoc=0

The RSS event page remains the source URL, but Register / View always uses
Mindbody.

## AZ Ice Gilbert

Gilbert is now configured as DaySmart facility ID 2, alongside:

- Peoria = 1
- Gilbert = 2
- Arcadia = 3

It uses the same DaySmart provider/cache logic as Peoria and Arcadia.

## IMPORTANT: refresh the SQLite cache

Existing cached events still contain their old registration URLs.

After replacing these files:

1. Let Uvicorn reload.
2. Click the website Refresh button once.
3. Wait until `/api/status` says `"refreshing": false`.
4. Hard-refresh Firefox with Ctrl + Shift + R.

Then verify `/api/status` includes `AZ Ice Gilbert`, and clicking an Ice Den
event opens Mindbody.

Suggested commit:

`Add Gilbert and finalize Kachina theme`
