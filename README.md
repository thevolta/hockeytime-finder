# Step 6.22 — Mullett Adult Skills source (based on 6.20)

Copy both files into your existing project:
- app/providers/sportified_provider.py
- app/config/sources.yaml

The site already has an Adult Skills checkbox, event color and popup from 6.20.
The source is the supplied Sportified product 24226, with direct registration links.

IMPORTANT: Sportified's product URL could not be fetched for verification.
This patch parses sessions only if the product page exposes schedule rows in
the same format as the other Mullett pages. If it doesn't, the provider needs
a different schedule endpoint or structured-data parser; this patch will not
invent dates or times. The product might be a single registration page without
schedule rows.

After deploying, refresh cache and inspect /api/events?rink=Mullett%20Arena
for event_type Adult Skills. Also inspect /api/status for provider errors.
