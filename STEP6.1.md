# Step 6.1 — Calendar styling + 10-event Quick View

## Replace

- `app/static/index.html`
- `app/static/app.js`
- `app/static/styles.css`

## Fixes

### Calendar

FullCalendar v7 no longer packages the calendar skeleton CSS inside its
JavaScript bundle. The app was loading:

`fullcalendar@7.0.2/all/global.js`

without:

`fullcalendar@7.0.2/skeleton.css`

This caused the calendar HTML to render without its actual grid/layout styles.

### Quick View

"Next sessions" now displays 10 events per page.

The heading includes:

- Previous
- Next
- `1–10 of 81` style page information

Changing rink/event filters automatically resets Quick View to page 1.

## Test

Refresh the browser using Ctrl+F5 after replacing the files so Firefox does not
reuse the old static files.

Suggested commit:

`Fix calendar layout and paginate quick view`
