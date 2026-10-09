# Step 6.22 revised — Mullett Adult Skills via Schedule
Based on Step 6.20. Replace app/providers/sportified_provider.py and app/config/sources.yaml.
Uses /schedule?date=YYYY-MM-DD in five seven-day windows; recognizes
'Adult Rookie Class' and 'Adult Skills' as Adult Skills calendar items.
Uses the supplied product 24226 as the registration link.
This parser is based on the publicly visible schedule text; verify results
after deployment by refreshing the cache. No frontend changes.
