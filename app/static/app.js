let rawEvents = [];
let calendar = null;

const UPCOMING_PAGE_SIZE = 10;
let upcomingPage = 0;

const colors = {
  "Stick Time": "#245f46",
  "Open Hockey": "#693a79",
  "Flow Hockey": "#7d202c",
};

const eventCount = document.getElementById("eventCount");
const statusText = document.getElementById("statusText");
const rinkFilter = document.getElementById("rinkFilter");
const viewSelect = document.getElementById("viewSelect");
const upcomingList = document.getElementById("upcomingList");
const refreshButton = document.getElementById("refreshButton");
const noWorkHours = document.getElementById("noWorkHours");
const filterAM = document.getElementById("filterAM");
const filterPM = document.getElementById("filterPM");

const upcomingPrev = document.getElementById("upcomingPrev");
const upcomingNext = document.getElementById("upcomingNext");
const upcomingPageInfo = document.getElementById("upcomingPageInfo");

const dialog = document.getElementById("eventDialog");
const dialogType = document.getElementById("dialogType");
const dialogTitle = document.getElementById("dialogTitle");
const dialogMeta = document.getElementById("dialogMeta");
const dialogRegister = document.getElementById("dialogRegister");
const dialogAddCalendar = document.getElementById("dialogAddCalendar");

function selectedTypes() {
  return [...document.querySelectorAll(".type-filter:checked")].map(el => el.value);
}

function arizonaMinutes(iso) {
  const date = new Date(iso);

  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Phoenix",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);

  const values = Object.fromEntries(
    parts
      .filter(part => part.type !== "literal")
      .map(part => [part.type, part.value])
  );

  return (Number(values.hour) * 60) + Number(values.minute);
}

function arizonaWeekday(iso) {
  const date = new Date(iso);

  const weekday = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Phoenix",
    weekday: "short",
  }).format(date);

  return weekday;
}

function overlapsWorkHours(event) {
  // "No work hours" only applies Monday-Friday.
  // Saturday and Sunday are always allowed.
  const weekday = arizonaWeekday(event.start);

  if (weekday === "Sat" || weekday === "Sun") {
    return false;
  }

  const workStart = 9 * 60;
  const workEnd = 16 * 60;

  const start = arizonaMinutes(event.start);

  // If an event has no explicit end time, assume one hour.
  const end = event.end
    ? arizonaMinutes(event.end)
    : start + 60;

  // Handle an event which crosses midnight.
  const normalizedEnd = end <= start ? end + (24 * 60) : end;

  return start < workEnd && normalizedEnd > workStart;
}

function matchesTimeOfDay(event) {
  const startMinutes = arizonaMinutes(event.start);
  const startsAM = startMinutes < (12 * 60);

  const showAM = Boolean(filterAM?.checked);
  const showPM = Boolean(filterPM?.checked);

  if (startsAM && showAM) return true;
  if (!startsAM && showPM) return true;

  return false;
}

function filteredEvents() {
  const types = selectedTypes();
  const rink = rinkFilter.value;
  const hideWorkHours = Boolean(noWorkHours?.checked);

  return rawEvents.filter(event => {
    const typeOk = types.includes(event.event_type);
    const rinkOk = !rink || event.rink === rink;
    const timeOfDayOk = matchesTimeOfDay(event);
    const workHoursOk = !hideWorkHours || !overlapsWorkHours(event);

    return typeOk && rinkOk && timeOfDayOk && workHoursOk;
  });
}

function upcomingEvents() {
  // Next Sessions intentionally uses filteredEvents(), so EVERY filter
  // (rink, event type, AM/PM, and No work hours) applies here too.
  return filteredEvents()
    .filter(e => new Date(e.start) >= new Date())
    .sort((a, b) => new Date(a.start) - new Date(b.start));
}

function displayTime(iso) {
  if (!iso) return "";
  return new Intl.DateTimeFormat([], {
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(iso));
}

function displayDate(iso) {
  return new Intl.DateTimeFormat([], {
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(new Date(iso));
}

function availabilityText(event) {
  if (Number.isInteger(event.open_slots) && event.open_slots >= 0) {
    return `${event.open_slots} spots shown available`;
  }

  if (Number.isInteger(event.capacity) && event.capacity > 0) {
    if (Number.isInteger(event.registered_count) && event.registered_count >= 0) {
      return `${Math.max(0, event.capacity - event.registered_count)} of ${event.capacity} spots calculated available`;
    }
    return `${event.capacity} player capacity`;
  }

  return "";
}

function fullCalendarEvents() {
  return filteredEvents().map(event => {
    let eventClass = "ht-event";

    if (event.event_type === "Stick Time") {
      eventClass += " ht-stick";
    } else if (event.event_type === "Open Hockey") {
      eventClass += " ht-open";
    } else if (event.event_type === "Flow Hockey") {
      eventClass += " ht-flow";
    }

    return {
      id: event.id,
      title: `${event.event_type} · ${event.rink}`,
      start: event.start,
      end: event.end,
      classNames: eventClass.split(" "),
      extendedProps: { source: event },
    };
  });
}

function populateRinks() {
  const current = rinkFilter.value;
  const rinks = [...new Set(rawEvents.map(e => e.rink))].sort();

  rinkFilter.innerHTML = '<option value="">All rinks</option>';

  for (const rink of rinks) {
    const option = document.createElement("option");
    option.value = rink;
    option.textContent = rink;
    rinkFilter.appendChild(option);
  }

  if (rinks.includes(current)) {
    rinkFilter.value = current;
  }
}

function resetUpcomingPage() {
  upcomingPage = 0;
}

function renderUpcoming() {
  const events = upcomingEvents();
  const totalPages = Math.max(1, Math.ceil(events.length / UPCOMING_PAGE_SIZE));

  if (upcomingPage >= totalPages) {
    upcomingPage = totalPages - 1;
  }

  const startIndex = upcomingPage * UPCOMING_PAGE_SIZE;
  const pageEvents = events.slice(
    startIndex,
    startIndex + UPCOMING_PAGE_SIZE
  );

  upcomingPrev.disabled = upcomingPage <= 0;
  upcomingNext.disabled = upcomingPage >= totalPages - 1 || events.length === 0;

  if (events.length) {
    upcomingPageInfo.textContent = `${startIndex + 1}–${Math.min(startIndex + UPCOMING_PAGE_SIZE, events.length)} of ${events.length}`;
  } else {
    upcomingPageInfo.textContent = "";
  }

  if (!pageEvents.length) {
    upcomingList.innerHTML =
      '<div class="empty">No upcoming events match these filters.</div>';
    return;
  }

  upcomingList.innerHTML = "";

  for (const event of pageEvents) {
    const item = document.createElement("article");
    item.className = "upcoming-item";

    const time = document.createElement("div");
    time.innerHTML = `
      <div class="upcoming-time">${displayTime(event.start)}</div>
      <div class="upcoming-date">${displayDate(event.start)}</div>
    `;

    const availability = availabilityText(event);

    const info = document.createElement("div");
    info.innerHTML = `
      <div class="upcoming-title">${escapeHtml(event.event_type)}</div>
      <div class="upcoming-rink">${escapeHtml(event.rink)}${event.city ? ` · ${escapeHtml(event.city)}` : ""}</div>
      ${availability ? `<div class="upcoming-rink">${escapeHtml(availability)}</div>` : ""}
    `;

    const action = document.createElement("button");
    action.className = "button secondary";
    action.type = "button";
    action.textContent = "Details";
    action.addEventListener("click", () => openEvent(event));

    item.append(time, info, action);
    upcomingList.appendChild(item);
  }
}

function renderAll(resetPage = false) {
  if (resetPage) {
    resetUpcomingPage();
  }

  eventCount.textContent = filteredEvents().length;

  calendar.removeAllEvents();
  calendar.addEventSource(fullCalendarEvents());

  renderUpcoming();
}

function openEvent(event) {
  dialogType.textContent = event.event_type;
  dialogTitle.textContent = event.title || event.event_type;

  const end = event.end ? `–${displayTime(event.end)}` : "";
  const availability = availabilityText(event);
  const status = event.registration_status
    ? `<div>Registration status: ${escapeHtml(event.registration_status)}</div>`
    : "";

  dialogMeta.innerHTML = `
    <div><strong>${escapeHtml(event.rink)}</strong></div>
    <div>${displayDate(event.start)} · ${displayTime(event.start)}${end}</div>
    <div>${[event.city, event.state].filter(Boolean).map(escapeHtml).join(", ")}</div>
    ${availability ? `<div><strong>${escapeHtml(availability)}</strong></div>` : ""}
    ${status}
  `;

  const destination = event.register_url || event.source_url;

  if (destination) {
    dialogRegister.href = destination;
    dialogRegister.style.display = "inline-block";
  } else {
    dialogRegister.style.display = "none";
  }

  dialogAddCalendar.onclick = () => downloadSingleEvent(event);
  dialog.showModal();
}

function downloadSingleEvent(event) {
  const start = new Date(event.start);
  const end = event.end
    ? new Date(event.end)
    : new Date(start.getTime() + 3600000);

  const toICS = date =>
    date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");

  const location = [event.rink, event.city, event.state]
    .filter(Boolean)
    .join(", ");

  const url = event.register_url || event.source_url || "";
  const description = url ? `Register / View: ${url}` : "";

  const ics = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//HockeyTime Finder//EN",
    "BEGIN:VEVENT",
    `UID:${event.id}@hockeytime-finder`,
    `DTSTAMP:${toICS(new Date())}`,
    `DTSTART:${toICS(start)}`,
    `DTEND:${toICS(end)}`,
    `SUMMARY:${icsEscape(`${event.event_type} - ${event.rink}`)}`,
    `LOCATION:${icsEscape(location)}`,
    `DESCRIPTION:${icsEscape(description)}`,
    url ? `URL:${url}` : "",
    "END:VEVENT",
    "END:VCALENDAR",
  ]
    .filter(Boolean)
    .join("\r\n");

  const blob = new Blob([ics], {
    type: "text/calendar;charset=utf-8",
  });

  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "hockeytime-event.ics";
  document.body.appendChild(link);
  link.click();
  link.remove();
}

function icsEscape(value) {
  return String(value || "")
    .replace(/\\/g, "\\\\")
    .replace(/\n/g, "\\n")
    .replace(/,/g, "\\,")
    .replace(/;/g, "\\;");
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatRefreshTime(iso) {
  if (!iso) {
    return "Cache has not completed its first refresh yet.";
  }

  return `Calendar cache updated ${new Date(iso).toLocaleString()}`;
}

async function loadEvents() {
  try {
    const response = await fetch("/api/events", {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }

    const data = await response.json();

    rawEvents = data.events || [];

    populateRinks();
    renderAll(true);

    if (data.cache?.refreshing) {
      statusText.className = "muted";
      statusText.textContent =
        "Refreshing rink calendars in the background…";
    } else {
      statusText.className = "muted";
      statusText.textContent = formatRefreshTime(
        data.cache?.last_successful_refresh
      );
    }
  } catch (error) {
    statusText.className = "error";
    statusText.textContent =
      `Could not load cached events: ${error.message}`;
  }
}

async function manualRefresh() {
  refreshButton.disabled = true;
  statusText.className = "muted";
  statusText.textContent = "Starting manual calendar refresh…";

  try {
    const response = await fetch("/api/refresh", {
      method: "POST",
      headers: {
        Accept: "application/json",
      },
    });

    const data = await response.json();

    if (response.status === 429) {
      statusText.className = "error";
      statusText.textContent =
        data.detail || "Refresh is temporarily unavailable.";
      return;
    }

    if (!response.ok) {
      throw new Error(
        data.detail || `API returned ${response.status}`
      );
    }

    statusText.className = "muted";
    statusText.textContent =
      "Refreshing rink calendars in the background…";

    for (let i = 0; i < 60; i++) {
      await new Promise(resolve => setTimeout(resolve, 2000));

      const statusResponse = await fetch("/api/status", {
        cache: "no-store",
      });

      const status = await statusResponse.json();

      if (!status.refreshing) {
        await loadEvents();
        return;
      }
    }

    statusText.textContent =
      "Refresh is still running; cached events remain available.";
  } catch (error) {
    statusText.className = "error";
    statusText.textContent =
      `Refresh failed: ${error.message}`;
  } finally {
    refreshButton.disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  calendar = new FullCalendar.Calendar(
    document.getElementById("calendar"),
    {
      initialView:
        window.innerWidth < 700 ? "listWeek" : "timeGridWeek",
      height: "auto",
      nowIndicator: true,
      firstDay: 0,
      slotMinTime: "06:00:00",
      slotMaxTime: "24:00:00",
      allDaySlot: false,
      dayMaxEvents: true,
      eventDisplay: "auto",
      eventTimeFormat: {
        hour: "numeric",
        minute: "2-digit",
      },
      headerToolbar: {
        left: "prev,next today",
        center: "title",
        right: "",
      },
      eventClick(info) {
        openEvent(info.event.extendedProps.source);
      },
    }
  );

  calendar.render();

  document.querySelectorAll(".type-filter").forEach(el => {
    el.addEventListener("change", () => renderAll(true));
  });

  rinkFilter.addEventListener("change", () => renderAll(true));

  noWorkHours?.addEventListener("change", () => renderAll(true));
  filterAM?.addEventListener("change", () => renderAll(true));
  filterPM?.addEventListener("change", () => renderAll(true));

  viewSelect.value = calendar.view.type;
  viewSelect.addEventListener("change", () => {
    calendar.changeView(viewSelect.value);
  });

  upcomingPrev.addEventListener("click", () => {
    if (upcomingPage > 0) {
      upcomingPage -= 1;
      renderUpcoming();
      document.querySelector(".upcoming-section")
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });

  upcomingNext.addEventListener("click", () => {
    const totalPages = Math.ceil(
      upcomingEvents().length / UPCOMING_PAGE_SIZE
    );

    if (upcomingPage < totalPages - 1) {
      upcomingPage += 1;
      renderUpcoming();
      document.querySelector(".upcoming-section")
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });

  refreshButton.addEventListener("click", manualRefresh);

  loadEvents();
});
