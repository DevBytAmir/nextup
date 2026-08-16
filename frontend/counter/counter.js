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
      <span class="eyebrow">Setup</span>
      <h1>Which counter are you?</h1>
      <div>
        <button id="select-1" class="btn-primary">Counter 1</button>
        <button id="select-2" class="btn-primary">Counter 2</button>
      </div>
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
      <span class="eyebrow">Now Serving</span>
      <h1>Counter ${counterId}</h1>
      <div id="current-number" class="led-number led-number--idle">—</div>
      <div class="button-row">
        <button id="call-next-btn" class="btn-primary">Call Next</button>
        <button id="done-btn" disabled>Done</button>
      </div>
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
    currentNumber.classList.remove("led-number--idle");
    currentNumber.textContent = `#${ticket.number}`;
    replayFlicker(currentNumber);
    message.textContent = "";
    callBtn.disabled = true;
    doneBtn.disabled = false;
  });

  doneBtn.addEventListener("click", async () => {
    const res = await apiPost("/api/counter/done", "counter", { counter: counterId });
    if (!res.ok) return;
    currentNumber.classList.add("led-number--idle");
    currentNumber.textContent = "—";
    callBtn.disabled = false;
    doneBtn.disabled = true;
  });
}

function replayFlicker(el) {
  el.style.animation = "none";
  void el.offsetWidth;
  el.style.animation = "";
}
