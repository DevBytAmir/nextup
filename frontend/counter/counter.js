initCounterFlow();

async function initCounterFlow() {
  if (getToken("counter")) {
    afterLogin();
    return;
  }
  const state = await (await apiGet("/api/state")).json();
  renderCounterSelect(state.counter_count);
}

function renderCounterSelect(counterCount) {
  const app = document.getElementById("app");
  const buttons = Array.from(
    { length: counterCount },
    (_, i) => `<button data-counter="${i + 1}" class="btn-primary">Counter ${i + 1}</button>`
  ).join("");
  app.innerHTML = `
    <div class="page counter-select">
      <span class="eyebrow">Setup</span>
      <h1>Which counter are you?</h1>
      <div>${buttons}</div>
    </div>
  `;
  app.querySelectorAll("[data-counter]").forEach((btn) => {
    btn.addEventListener("click", () => renderCounterPinPad(Number(btn.dataset.counter)));
  });
}

function renderCounterPinPad(counterId) {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="pin-pad">
      <span class="eyebrow">Counter ${counterId}</span>
      <h1>Enter PIN</h1>
      <input type="password" id="pin-input" inputmode="numeric" autocomplete="off" maxlength="8" />
      <button id="pin-submit" class="btn-primary">Enter</button>
      <p id="pin-error" class="error hidden">Wrong PIN</p>
      <button id="pin-back" class="link-btn">Back</button>
    </div>
  `;
  const input = document.getElementById("pin-input");
  const error = document.getElementById("pin-error");

  async function submit() {
    const pin = input.value.trim();
    if (!pin) return;
    const ok = await login("counter", pin, counterId);
    if (ok) {
      afterLogin();
    } else {
      error.classList.remove("hidden");
      input.value = "";
    }
  }

  document.getElementById("pin-submit").addEventListener("click", submit);
  document.getElementById("pin-back").addEventListener("click", initCounterFlow);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") submit();
  });
  input.focus();
}

async function afterLogin() {
  const whoRes = await apiGetAuthed("/api/counter/whoami", "counter");
  if (!whoRes.ok) return;
  const { counter: counterId } = await whoRes.json();
  const state = await (await apiGet("/api/state")).json();
  renderCounter(counterId, state);
}

function renderCounter(counterId, state) {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="page counter-page">
      <span class="eyebrow">Now Serving</span>
      <h1>Counter ${counterId}</h1>
      <div id="current-number" class="led-number led-number--idle">—</div>
      <div class="button-row">
        <button id="call-next-btn" class="btn-primary">Call Next</button>
        <button id="recall-btn">Call Previous</button>
        <button id="done-btn" disabled>Done</button>
      </div>
      <p id="counter-message"></p>
      <button id="switch-counter-btn" class="link-btn">Switch counter</button>
    </div>
  `;
  document.getElementById("switch-counter-btn").addEventListener("click", () => {
    clearToken("counter");
    initCounterFlow();
  });
  const currentNumber = document.getElementById("current-number");
  const callBtn = document.getElementById("call-next-btn");
  const recallBtn = document.getElementById("recall-btn");
  const doneBtn = document.getElementById("done-btn");
  const message = document.getElementById("counter-message");

  function showActive(ticket) {
    currentNumber.classList.remove("led-number--idle");
    currentNumber.textContent = `#${ticket.number}`;
    replayFlicker(currentNumber);
    message.textContent = "";
    callBtn.disabled = true;
    recallBtn.disabled = true;
    doneBtn.disabled = false;
  }

  function showIdle() {
    currentNumber.classList.add("led-number--idle");
    currentNumber.textContent = "—";
    callBtn.disabled = false;
    recallBtn.disabled = false;
    doneBtn.disabled = true;
  }

  callBtn.addEventListener("click", async () => {
    const res = await apiPost("/api/counter/call-next", "counter");
    if (res.status === 409) {
      const body = await res.json().catch(() => null);
      message.textContent =
        body?.detail === "this counter already has an active ticket"
          ? "You already have an active ticket"
          : "No one waiting";
      return;
    }
    if (!res.ok) return;
    showActive(await res.json());
  });

  recallBtn.addEventListener("click", async () => {
    const res = await apiPost("/api/counter/recall-previous", "counter");
    if (res.status === 404) {
      message.textContent = "Nothing to recall";
      return;
    }
    if (!res.ok) return;
    showActive(await res.json());
  });

  doneBtn.addEventListener("click", async () => {
    const res = await apiPost("/api/counter/done", "counter");
    if (!res.ok) return;
    showIdle();
  });

  const activeTicket = state.tickets.find(
    (t) => t.status === "called" && t.counter === counterId
  );
  if (activeTicket) {
    showActive(activeTicket);
  }
}

function replayFlicker(el) {
  el.style.animation = "none";
  void el.offsetWidth;
  el.style.animation = "";
}
