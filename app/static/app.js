let rawEvents = [];
let calendar = null;

const colors = {
  "Stick Time": "#49c58b",
  "Open Hockey": "#5fa8ff",
  "Flow Hockey": "#b58cff",
};

const eventCount = document.getElementById("eventCount");
const statusText = document.getElementById("statusText");
const rinkFilter = document.getElementById("rinkFilter");
const viewSelect = document.getElementById("viewSelect");
const upcomingList = document.getElementById("upcomingList");
const refreshButton = document.getElementById("refreshButton");

const dialog = document.getElementById("eventDialog");
const dialogType = document.getElementById("dialogType");
const dialogTitle = document.getElementById("dialogTitle");
const dialogMeta = document.getElementById("dialogMeta");
const dialogRegister = document.getElementById("dialogRegister");
const dialogAddCalendar = document.getElementById("dialogAddCalendar");

function selectedTypes() {
  return [...document.querySelectorAll(".type-filter:checked")].map(el => el.value);
}

function filteredEvents() {
  const types = selectedTypes();
  const rink = rinkFilter.value;

  return rawEvents.filter(event => {
    const typeOk = types.includes(event.event_type);
    const rinkOk = !rink || event.rink === rink;
    return typeOk && rinkOk;
  });
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

function fullCalendarEvents() {
  return filteredEvents().map(event => ({
    id: event.id,
    title: `${event.event_type} · ${event.rink}`,
    start: event.start,
    end: event.end,
    backgroundColor: colors[event.event_type] || "#5fa8ff",
    borderColor: colors[event.event_type] || "#5fa8ff",
    textColor: "#07101d",
    extendedProps: { source: event },
  }));
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
  if (rinks.includes(current)) rinkFilter.value = current;
}

function renderUpcoming() {
  const events = filteredEvents()
    .filter(e => new Date(e.start) >= new Date())
    .sort((a, b) => new Date(a.start) - new Date(b.start))
    .slice(0, 12);

  if (!events.length) {
    upcomingList.innerHTML = '<div class="empty">No upcoming events match these filters.</div>';
    return;
  }

  upcomingList.innerHTML = "";
  for (const event of events) {
    const item = document.createElement("article");
    item.className = "upcoming-item";

    const time = document.createElement("div");
    time.innerHTML = `
      <div class="upcoming-time">${displayTime(event.start)}</div>
      <div class="upcoming-date">${displayDate(event.start)}</div>
    `;

    const info = document.createElement("div");
    info.innerHTML = `
      <div class="upcoming-title">${escapeHtml(event.event_type)}</div>
      <div class="upcoming-rink">${escapeHtml(event.rink)}${event.city ? ` · ${escapeHtml(event.city)}` : ""}</div>
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

function renderAll() {
  const filtered = filteredEvents();
  eventCount.textContent = filtered.length;
  calendar.removeAllEvents();
  calendar.addEventSource(fullCalendarEvents());
  renderUpcoming();
}

function openEvent(event) {
  dialogType.textContent = event.event_type;
  dialogTitle.textContent = event.title || event.event_type;

  const end = event.end ? `–${displayTime(event.end)}` : "";
  dialogMeta.innerHTML = `
    <div><strong>${escapeHtml(event.rink)}</strong></div>
    <div>${displayDate(event.start)} · ${displayTime(event.start)}${end}</div>
    <div>${[event.city, event.state].filter(Boolean).map(escapeHtml).join(", ")}</div>
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
  const end = event.end ? new Date(event.end) : new Date(start.getTime() + 60 * 60 * 1000);

  const toICS = date => date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
  const location = [event.rink, event.city, event.state].filter(Boolean).join(", ");
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
  ].filter(Boolean).join("\r\n");

  const blob = new Blob([ics], { type: "text/calendar;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "hockeytime-event.ics";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(link.href);
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

async function loadEvents() {
  statusText.className = "muted";
  statusText.textContent = "Loading schedules…";
  refreshButton.disabled = true;

  try {
    const response = await fetch("/api/events", { cache: "no-store" });
    if (!response.ok) throw new Error(`API returned ${response.status}`);

    const data = await response.json();
    rawEvents = data.events || [];
    populateRinks();
    renderAll();

    if (data.errors && data.errors.length) {
      const names = data.errors.map(e => e.source).join(", ");
      statusText.className = "error";
      statusText.textContent = `Loaded with source errors: ${names}`;
    } else {
      statusText.className = "muted";
      statusText.textContent = `Updated ${new Date().toLocaleTimeString([], {hour: "numeric", minute: "2-digit"})}`;
    }
  } catch (error) {
    console.error(error);
    statusText.className = "error";
    statusText.textContent = `Could not load events: ${error.message}`;
  } finally {
    refreshButton.disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const calendarEl = document.getElementById("calendar");

  calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: window.innerWidth < 700 ? "listWeek" : "timeGridWeek",
    height: "auto",
    nowIndicator: true,
    firstDay: 0,
    slotMinTime: "06:00:00",
    slotMaxTime: "24:00:00",
    allDaySlot: false,
    eventTimeFormat: { hour: "numeric", minute: "2-digit" },
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: "",
    },
    eventClick(info) {
      openEvent(info.event.extendedProps.source);
    },
  });

  calendar.render();

  document.querySelectorAll(".type-filter").forEach(el => {
    el.addEventListener("change", renderAll);
  });

  rinkFilter.addEventListener("change", renderAll);

  viewSelect.value = calendar.view.type;
  viewSelect.addEventListener("change", () => {
    calendar.changeView(viewSelect.value);
  });

  refreshButton.addEventListener("click", loadEvents);

  loadEvents();
});
