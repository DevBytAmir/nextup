function renderPinPad(container, page, onSuccess) {
  container.innerHTML = `
    <div class="pin-pad">
      <span class="eyebrow">Staff Access</span>
      <h1>Enter PIN</h1>
      <input type="password" id="pin-input" inputmode="numeric" autocomplete="off" maxlength="8" />
      <button id="pin-submit" class="btn-primary">Enter</button>
      <p id="pin-error" class="error hidden">Wrong PIN</p>
    </div>
  `;
  const input = container.querySelector("#pin-input");
  const button = container.querySelector("#pin-submit");
  const error = container.querySelector("#pin-error");

  async function submit() {
    const pin = input.value.trim();
    if (!pin) return;
    const ok = await login(page, pin);
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
