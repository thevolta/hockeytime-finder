# HockeyTime Finder

FastAPI backend for aggregating hockey sessions from multiple rink providers.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:

- API docs: http://127.0.0.1:8000/docs
- Events: http://127.0.0.1:8000/api/events
- Calendar feed: http://127.0.0.1:8000/calendar.ics

## Current provider types

- RSS
- Sportified
- DaySmart (scaffold / config-ready)

## Next steps

1. Finish provider-specific parsing.
2. Add scheduled refresh into SQLite.
3. Add React frontend.
4. Deploy backend and frontend.
