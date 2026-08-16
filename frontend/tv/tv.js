initTvPage();

function initTvPage() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="page tv-page">
      <div class="counters">
        <div class="counter-tile"><h2>Counter 1</h2><div id="counter-1-number">—</div></div>
        <div class="counter-tile"><h2>Counter 2</h2><div id="counter-2-number">—</div></div>
      </div>
      <div id="waiting-count">Waiting: 0</div>
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
  const called = { 1: "—", 2: "—" };
  for (const ticket of state.tickets) {
    if (ticket.status === "called" && (ticket.counter === 1 || ticket.counter === 2)) {
      called[ticket.counter] = ticket.number;
    }
  }
  document.getElementById("counter-1-number").textContent = displayNumber(called[1]);
  document.getElementById("counter-2-number").textContent = displayNumber(called[2]);

  const waitingCount = state.tickets.filter((t) => t.status === "waiting").length;
  document.getElementById("waiting-count").textContent = `Waiting: ${waitingCount}`;

  const recent = state.tickets
    .filter((t) => t.status === "called" || t.status === "served")
    .sort((a, b) => b.number - a.number)
    .slice(0, 5);
  document.getElementById("recent-list").innerHTML = recent
    .map((t) => `<li>#${t.number} — ${t.status}</li>`)
    .join("");
}

function displayNumber(value) {
  return value === "—" ? "—" : `#${value}`;
}
