requireAuth("admin", initAdminPage);

function initAdminPage() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="page admin-page">
      <span class="eyebrow">Control Panel</span>
      <h1>Admin</h1>
      <section id="ticket-table"></section>
      <section class="settings-panel">
        <h2>Counter PINs</h2>
        <input id="counter1-pin" placeholder="New Counter 1 PIN" />
        <button id="save-counter1">Save</button>
        <input id="counter2-pin" placeholder="New Counter 2 PIN" />
        <button id="save-counter2">Save</button>
        <p id="settings-message"></p>
      </section>
    </div>
  `;
  document
    .getElementById("save-counter1")
    .addEventListener("click", () => saveSetting("counter1_pin", "counter1-pin"));
  document
    .getElementById("save-counter2")
    .addEventListener("click", () => saveSetting("counter2_pin", "counter2-pin"));

  apiGet("/api/state")
    .then((res) => res.json())
    .then(renderTickets);
  connectWs(renderTickets);
}

async function saveSetting(field, inputId) {
  const value = document.getElementById(inputId).value.trim();
  if (!value) return;
  const res = await apiPost("/api/admin/settings", "admin", { [field]: value });
  document.getElementById("settings-message").textContent = res.ok ? "Saved" : "Failed to save";
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
  }
  if (status === "skipped") {
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
