function renderPinPad(container, page, onSuccess, options = {}) {
  const { eyebrow = "Staff Access", counter, onBack } = options;
  container.innerHTML = `
    <div class="pin-pad">
      <span class="eyebrow">${eyebrow}</span>
      <h1>Enter PIN</h1>
      <input type="password" id="pin-input" inputmode="numeric" autocomplete="off" maxlength="8" />
      <button id="pin-submit" class="btn-primary">Enter</button>
      <p id="pin-error" class="error hidden">Wrong PIN</p>
      ${onBack ? '<button id="pin-back" class="link-btn">Back</button>' : ""}
    </div>
  `;
  const input = container.querySelector("#pin-input");
  const button = container.querySelector("#pin-submit");
  const error = container.querySelector("#pin-error");

  async function submit() {
    const pin = input.value.trim();
    if (!pin) return;
    const ok = await login(page, pin, counter);
    if (ok) {
      onSuccess();
    } else {
      error.classList.remove("hidden");
      input.value = "";
    }
  }

  button.addEventListener("click", submit);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") submit();
  });
  if (onBack) {
    container.querySelector("#pin-back").addEventListener("click", onBack);
  }
  input.focus();
}

function requireAuth(page, onReady) {
  const container = document.getElementById("app");
  if (getToken(page)) {
    onReady();
    return;
  }
  renderPinPad(container, page, () => {
    container.innerHTML = "";
    onReady();
  });
}
