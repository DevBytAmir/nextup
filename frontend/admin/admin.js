requireAuth("admin", initAdminPage);

let currentCounterCount = 0;

async function initAdminPage() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="page admin-page">
      <span class="eyebrow">Control Panel</span>
      <h1>Admin</h1>
      <section id="ticket-table"></section>
      <section class="settings-panel">
        <h2>Issue Numbers</h2>
        <label for="bulk-issue-count">How many numbers to issue at once</label>
        <input id="bulk-issue-count" type="number" min="1" max="200" value="1" />
        <button id="issue-bulk" class="btn-primary">Issue Numbers</button>
        <p id="issue-bulk-message"></p>
      </section>
      <section class="settings-panel">
        <h2>Counters</h2>
        <label for="counter-count-input">Number of counters</label>
        <input id="counter-count-input" type="number" min="1" value="2" />
        <div id="counter-pin-inputs"></div>
        <button id="save-counters" class="btn-primary">Save Counters</button>
        <p id="settings-message"></p>
      </section>
      <section class="settings-panel">
        <h2>Sound</h2>
        <label>What plays on the TV screen when a number is called</label>
        <div class="radio-group">
          <label><input type="radio" name="sound-mode" value="off" /> Off</label>
          <label><input type="radio" name="sound-mode" value="beep" /> Beep</label>
          <label><input type="radio" name="sound-mode" value="announce" /> Voice announce</label>
        </div>
        <button id="save-sound" class="btn-primary">Save Sound</button>
        <p id="sound-message"></p>
      </section>
    </div>
  `;

  const state = await (await apiGet("/api/state")).json();
  currentCounterCount = state.counter_count;
  const countInput = document.getElementById("counter-count-input");
  countInput.value = currentCounterCount;
  renderPinInputs(currentCounterCount);

  countInput.addEventListener("input", () => {
    const count = Math.max(1, Number(countInput.value) || 1);
    renderPinInputs(count);
  });

  document.getElementById("issue-bulk").addEventListener("click", issueBulk);

  document.getElementById("save-counters").addEventListener("click", saveCounters);

  document.querySelectorAll('input[name="sound-mode"]').forEach((input) => {
    input.checked = input.value === state.sound_mode;
  });
  document.getElementById("save-sound").addEventListener("click", saveSoundMode);

  renderTickets(state);
  connectWs(renderTickets);
}

async function issueBulk() {
  const input = document.getElementById("bulk-issue-count");
  const message = document.getElementById("issue-bulk-message");
  const count = Number(input.value);
  if (!Number.isInteger(count) || count < 1) {
    message.textContent = "Enter a number of 1 or more";
    return;
  }
  const res = await apiPost("/api/admin/issue-bulk", "admin", { count });
  if (!res.ok) {
    message.textContent = "Failed to issue numbers";
    return;
  }
  const { tickets } = await res.json();
  message.textContent = `Issued #${tickets[0].number} to #${tickets[tickets.length - 1].number}`;
}

async function saveSoundMode() {
  const selected = document.querySelector('input[name="sound-mode"]:checked');
  const message = document.getElementById("sound-message");
  if (!selected) {
    message.textContent = "Pick a sound option";
    return;
  }
  const res = await apiPost("/api/admin/sound-mode", "admin", { sound_mode: selected.value });
  message.textContent = res.ok ? "Saved" : "Failed to save";
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[ch]);
}

function renderPinInputs(count) {
  const container = document.getElementById("counter-pin-inputs");
  const existing = Array.from(container.querySelectorAll("input")).map((el) => el.value);
  container.innerHTML = Array.from({ length: count }, (_, i) => {
    const placeholder =
      i < currentCounterCount ? "Leave blank to keep current PIN" : `New counter ${i + 1} PIN`;
    return `<input data-pin-index="${i}" placeholder="${placeholder}" value="${escapeHtml(existing[i] || "")}" />`;
  }).join("");
}

async function saveCounters() {
  const pins = Array.from(document.querySelectorAll("[data-pin-index]")).map((el) =>
    el.value.trim()
  );
  const message = document.getElementById("settings-message");
  const missingNewPin = pins.some((p, i) => !p && i >= currentCounterCount);
  if (!pins.length || missingNewPin) {
    message.textContent = "New counters need a PIN";
    return;
  }
  const res = await apiPost("/api/admin/counters", "admin", { counter_pins: pins });
  message.textContent = res.ok ? "Saved" : "Failed to save";
  if (res.ok) {
    currentCounterCount = pins.length;
    document.querySelectorAll("[data-pin-index]").forEach((el) => (el.value = ""));
    renderPinInputs(currentCounterCount);
  }
}

function renderTickets(state) {
  const container = document.getElementById("ticket-table");
  const groups = { waiting: [], called: [], served: [], skipped: [] };
  for (const ticket of state.tickets) {
    groups[ticket.status].push(ticket);
  }
  groups.waiting.sort((a, b) => a.order - b.order);

  container.innerHTML = Object.entries(groups)
    .map(
      ([status, tickets]) => `
      <div class="ticket-group">
        <h2><span class="status-pill status-pill--${status}">${status}</span> · ${tickets.length}</h2>
        <ul>${tickets.map((t) => ticketRow(t, status)).join("")}</ul>
      </div>
    `
    )
    .join("");

  container.querySelectorAll("[data-action]").forEach((el) => {
    el.addEventListener("click", () =>
      handleAction(el.dataset.action, Number(el.dataset.number), el.dataset.direction)
    );
  });
}

function ticketRow(ticket, status) {
  const actions = [];
  if (status === "waiting") {
    actions.push(
      `<button data-action="reorder" data-number="${ticket.number}" data-direction="up">↑</button>`
    );
    actions.push(
      `<button data-action="reorder" data-number="${ticket.number}" data-direction="down">↓</button>`
    );
    actions.push(`<button data-action="skip" data-number="${ticket.number}">Skip</button>`);
  }
  if (status === "called") {
    actions.push(`<button data-action="skip" data-number="${ticket.number}">Skip</button>`);
    actions.push(`<button data-action="requeue" data-number="${ticket.number}">Requeue</button>`);
  }
  if (status === "served" || status === "skipped") {
    actions.push(`<button data-action="requeue" data-number="${ticket.number}">Requeue</button>`);
  }
  actions.push(`<button data-action="delete" data-number="${ticket.number}">Delete</button>`);
  return `<li><span class="ticket-number">#${ticket.number}</span> ${actions.join(" ")}</li>`;
}

async function handleAction(action, number, direction) {
  const paths = {
    skip: "/api/admin/skip",
    requeue: "/api/admin/requeue",
    delete: "/api/admin/delete",
    reorder: "/api/admin/reorder",
  };
  const body = action === "reorder" ? { number, direction } : { number };
  await apiPost(paths[action], "admin", body);
}
