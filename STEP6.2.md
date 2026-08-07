# Step 6.2 — Proper FullCalendar v7 theme

FullCalendar v7 requires:

- `skeleton.css`
- a theme JS plugin
- a theme stylesheet
- a theme palette

Step 6.1 only added `skeleton.css`, which produced the partially-styled
calendar seen in testing.

## Replace

- `app/static/index.html`
- `app/static/app.js`
- `app/static/styles.css`

This patch uses the FullCalendar v7 Classic theme and applies HockeyTime
Finder's dark UI overrides.

After replacing the files:

1. Let Uvicorn reload.
2. Press Ctrl+F5 in Firefox.

Suggested commit:

`Fix FullCalendar v7 theme styling`
