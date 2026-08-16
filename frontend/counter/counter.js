requireAuth("counter", initCounterPage);

function initCounterPage() {
  const counterId = localStorage.getItem("queue_counter_id");
  if (!counterId) {
    renderCounterSelect();
    return;
  }
  renderCounter(Number(counterId));
}

function renderCounterSelect() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="page counter-select">
      <h1>Which counter are you?</h1>
      <button id="select-1">Counter 1</button>
      <button id="select-2">Counter 2</button>
    </div>
  `;
  document.getElementById("select-1").addEventListener("click", () => chooseCounter(1));
  document.getElementById("select-2").addEventListener("click", () => chooseCounter(2));
}

function chooseCounter(id) {
  localStorage.setItem("queue_counter_id", String(id));
  renderCounter(id);
}

function renderCounter(counterId) {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="page counter-page">
      <h1>Counter ${counterId}</h1>
      <div id="current-number">—</div>
      <button id="call-next-btn">Call Next</button>
      <button id="done-btn" disabled>Done</button>
      <p id="counter-message"></p>
    </div>
  `;
  const currentNumber = document.getElementById("current-number");
  const callBtn = document.getElementById("call-next-btn");
  const doneBtn = document.getElementById("done-btn");
  const message = document.getElementById("counter-message");

  callBtn.addEventListener("click", async () => {
    const res = await apiPost("/api/counter/call-next", "counter", { counter: counterId });
    if (res.status === 409) {
      message.textContent = "No one waiting";
      return;
    }
    if (!res.ok) return;
    const ticket = await res.json();
    currentNumber.textContent = `#${ticket.number}`;
    message.textContent = "";
    callBtn.disabled = true;
    doneBtn.disabled = false;
  });

  doneBtn.addEventListener("click", async () => {
    const res = await apiPost("/api/counter/done", "counter", { counter: counterId });
    if (!res.ok) return;
    currentNumber.textContent = "—";
    callBtn.disabled = false;
    doneBtn.disabled = true;
  });
}
