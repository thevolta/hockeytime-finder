# Step 3 update

Replace these three files in your existing repo:

- `app/providers/sportified_provider.py`
- `app/providers/daysmart_provider.py`
- `app/api/routes.py`
- `app/config/sources.yaml`

Then restart the API:

```powershell
uvicorn app.main:app --reload
```

Test:

- `http://127.0.0.1:8000/api/events`
- `http://127.0.0.1:8000/api/events?rink=Mullett`
- `http://127.0.0.1:8000/api/diagnostics/daysmart`

The DaySmart diagnostic endpoint is important. It shows the actual iframe URL
discovered from the AZ Ice public event pages and a sample of what DaySmart
returns to a normal server-side request.

If `calendar_text_sample` contains Stick Time / Pickup Hockey events, the
DaySmart provider should begin returning them automatically. If it only returns
an app shell, copy the JSON from `/api/diagnostics/daysmart` back into ChatGPT
and we can wire the exact browser API request next.
