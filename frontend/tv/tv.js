initTvPage();

let renderedCount = 0;

function initTvPage() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="page tv-page">
      <span class="eyebrow">Live Queue</span>
      <div class="counters" id="counters"></div>
      <div id="waiting-count">Waiting <span class="led-number">0</span></div>
      <div class="recent">
        <h2>Recently Called</h2>
        <ul id="recent-list"></ul>
      </div>
    </div>
  `;
  apiGet("/api/state")
    .then((res) => res.json())
    .then(render);
  connectWs(render);
}

function render(state) {
  if (state.counter_count !== renderedCount) {
    renderCounterTiles(state.counter_count);
  }

  const called = {};
  for (const ticket of state.tickets) {
    if (ticket.status === "called" && ticket.counter) {
      called[ticket.counter] = ticket.number;
    }
  }
  for (let i = 1; i <= state.counter_count; i++) {
    updateCounterTile(i, called[i] ?? "—");
  }

  const waitingCount = state.tickets.filter((t) => t.status === "waiting").length;
  document.getElementById("waiting-count").innerHTML =
    `Waiting <span class="led-number">${waitingCount}</span>`;

  const recent = state.tickets
    .filter((t) => t.status === "called" || t.status === "served")
    .sort((a, b) => b.number - a.number)
    .slice(0, 5);
  document.getElementById("recent-list").innerHTML = recent
    .map((t) => `<li>#${t.number} <span class="status-pill status-pill--${t.status}">${t.status}</span></li>`)
    .join("");
}

function renderCounterTiles(counterCount) {
  const container = document.getElementById("counters");
  container.innerHTML = Array.from(
    { length: counterCount },
    (_, i) => `
      <div class="counter-tile">
        <h2>Counter ${i + 1}</h2>
        <div id="counter-${i + 1}-number" class="led-number led-number--idle">—</div>
      </div>
    `
  ).join("");
  renderedCount = counterCount;
}

function updateCounterTile(counterId, value) {
  const el = document.getElementById(`counter-${counterId}-number`);
  if (!el) return;
  const next = displayNumber(value);
  if (el.textContent === next) return;
  el.textContent = next;
  el.classList.toggle("led-number--idle", value === "—");
  el.style.animation = "none";
  void el.offsetWidth;
  el.style.animation = "";
}

function displayNumber(value) {
  return value === "—" ? "—" : `#${value}`;
}
