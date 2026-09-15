const POLL_INTERVAL_MS = 10000;

let renderedCounterCount = 0;
let previousCalled = {};
let hasRenderedOnce = false;
let audioCtx = null;
let audioUnlocked = false;

initTvPage();

function initTvPage() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="page tv-page">
      <div class="tv-header">
        <span class="eyebrow">Live Queue</span>
        <h1>Now Serving</h1>
      </div>
      <div class="counters" id="counters"></div>
      <div id="waiting-count">Waiting <span class="led-number">0</span></div>
      <p id="tv-status" class="tv-status hidden"></p>
      <div class="recent">
        <h2>Recently Called</h2>
        <ul id="recent-list"></ul>
      </div>
      <p id="tv-unlock-hint" class="tv-unlock-hint">Tap anywhere on this screen once to enable sound</p>
    </div>
  `;

  // Browsers block audio playback until the page has been physically
  // touched/clicked at least once. A TV display never gets a natural
  // click, so without this the sound setting would silently do nothing.
  document.addEventListener("click", unlockAudio, { once: true });
  document.addEventListener("touchstart", unlockAudio, { once: true });

  loadAndRender();
  connectWs(render);
  // A WebSocket can die without ever firing `close` on some networks/TV
  // hardware. Poll independently so the screen recovers either way.
  setInterval(loadAndRender, POLL_INTERVAL_MS);
}

function unlockAudio() {
  if (audioUnlocked) return;
  audioUnlocked = true;
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (Ctx) {
      if (!audioCtx) audioCtx = new Ctx();
      audioCtx.resume();
    }
  } catch {
    // Web Audio unavailable: beep will just stay silent
  }
  try {
    if (typeof speechSynthesis !== "undefined") {
      speechSynthesis.speak(new SpeechSynthesisUtterance(""));
    }
  } catch {
    // speech synthesis unavailable: announce will just stay silent
  }
  document.getElementById("tv-unlock-hint")?.classList.add("hidden");
}

function loadAndRender() {
  const statusEl = document.getElementById("tv-status");
  apiGet("/api/state")
    .then((res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    })
    .then((state) => {
      statusEl.classList.add("hidden");
      render(state);
    })
    .catch((err) => {
      statusEl.textContent = `Connection issue, retrying... (${err.message})`;
      statusEl.classList.remove("hidden");
    });
}

function announce(soundMode, text) {
  if (soundMode === "announce") {
    speak(text);
  } else if (soundMode === "beep") {
    beep();
  }
}

function speak(text) {
  if (typeof speechSynthesis === "undefined") return;
  speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.95;
  speechSynthesis.speak(utterance);
}

function beep() {
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return;
    if (!audioCtx) audioCtx = new Ctx();
    if (audioCtx.state === "suspended") audioCtx.resume();
    // A short two-note "ding-dong" chime, like a PA announcement bell.
    playTone(1046.5, audioCtx.currentTime, 0.22);
    playTone(783.99, audioCtx.currentTime + 0.2, 0.32);
  } catch {
    // audio unavailable/blocked: the visual update already happened
  }
}

function playTone(frequency, startTime, duration) {
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.type = "sine";
  osc.frequency.value = frequency;
  gain.gain.setValueAtTime(0.0001, startTime);
  gain.gain.exponentialRampToValueAtTime(0.3, startTime + 0.02);
  gain.gain.exponentialRampToValueAtTime(0.0001, startTime + duration);
  osc.connect(gain).connect(audioCtx.destination);
  osc.start(startTime);
  osc.stop(startTime + duration + 0.02);
}

function render(state) {
  if (state.counter_count !== renderedCounterCount) {
    renderCounterTiles(state.counter_count);
  }

  const called = {};
  for (const ticket of state.tickets) {
    if (ticket.status === "called" && ticket.counter) {
      called[ticket.counter] = ticket.number;
    }
  }

  for (let counter = 1; counter <= state.counter_count; counter++) {
    const value = called[counter] ?? "—";
    updateCounterTile(counter, value);
    if (hasRenderedOnce && value !== "—" && value !== previousCalled[counter]) {
      announce(state.sound_mode, `Number ${value}, please go to counter ${counter}`);
    }
  }
  previousCalled = called;
  hasRenderedOnce = true;

  const waitingCount = state.tickets.filter((t) => t.status === "waiting").length;
  document.getElementById("waiting-count").innerHTML =
    `Waiting <span class="led-number">${waitingCount}</span>`;

  const recent = state.tickets
    .filter((t) => t.status === "called" || t.status === "served")
    .sort((a, b) => b.touched_at - a.touched_at)
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
  renderedCounterCount = counterCount;
}

function updateCounterTile(counterId, value) {
  const el = document.getElementById(`counter-${counterId}-number`);
  if (!el) return;
  const next = value === "—" ? "—" : `#${value}`;
  if (el.textContent === next) return;
  el.textContent = next;
  el.classList.toggle("led-number--idle", value === "—");
  el.style.animation = "none";
  void el.offsetWidth;
  el.style.animation = "";
}
