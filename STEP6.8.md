# Step 6.8 — Simple dark theme

This intentionally removes the Kachina styling and stops fighting
FullCalendar's own event colors.

## Replace

- `app/static/index.html`
- `app/static/app.js`
- `app/static/styles.css`

## Important change

Events are now assigned explicit CSS classes:

- `.ht-stick`
- `.ht-open`
- `.ht-flow`

The colors are forced with `!important`, so FullCalendar can no longer replace
them with the default blue event color.

The FullCalendar Classic theme assets are also removed. Only the core/skeleton
CSS is used, with HockeyTime Finder providing the dark styling.

## Test

After copying the files:

1. Let Uvicorn reload.
2. Hard refresh Firefox with `Ctrl + Shift + R`.
3. Week view should have dark gray cells.
4. Stick Time should be green.
5. Open Hockey should be purple.
6. Flow Hockey should be red/maroon.

Suggested commit:

`Simplify calendar dark theme`
