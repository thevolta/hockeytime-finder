# Step 6.9 — Fix calendar with FullCalendar 6 + Kachina colors

The calendar layout broke because the frontend was using FullCalendar v7's new
CSS architecture.

This patch moves the frontend to:

FullCalendar 6.1.19

The v6 global bundle includes the required calendar layout styling, so the week
and month views render correctly again.

## Replace

- `app/static/index.html`
- `app/static/app.js`
- `app/static/styles.css`

## Theme

No images or logos are used.

Palette only:

- charcoal / black background
- deep maroon controls and headers
- cream text
- forest green accents
- purple Open Hockey events

Event colors:

- Stick Time = forest green
- Open Hockey = purple
- Flow Hockey = dark maroon

## After copying

1. Let Uvicorn reload.
2. Open Firefox DevTools > Network.
3. Enable "Disable Cache" temporarily if desired.
4. Hard refresh with Ctrl + Shift + R.

The browser should load:

https://cdn.jsdelivr.net/npm/fullcalendar@6.1.19/index.global.min.js

There should be no FullCalendar v7 CSS or JS remaining.

Suggested commit:

`Fix calendar with FullCalendar 6`
