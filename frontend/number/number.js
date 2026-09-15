requireAuth("number", initNumberPage);

function initNumberPage() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="page number-page">
      <span class="eyebrow">Now Issuing</span>
      <h1>Issue Number</h1>
      <button id="issue-btn" class="btn-primary">Take a Number</button>
      <div id="last-issued"></div>
      <ul id="recent-list"></ul>
      <button id="logout-btn" class="link-btn">Log out</button>
    </div>
  `;
  const recentList = document.getElementById("recent-list");
  const lastIssued = document.getElementById("last-issued");
  const issued = [];

  document.getElementById("logout-btn").addEventListener("click", async () => {
    await logout("number");
    location.reload();
  });

  document.getElementById("issue-btn").addEventListener("click", async () => {
    const res = await apiPost("/api/number/issue", "number");
    if (!res.ok) return;
    const ticket = await res.json();
    issued.unshift(ticket.number);
    issued.length = Math.min(issued.length, 5);
    lastIssued.innerHTML = `Last issued <span class="led-number">#${ticket.number}</span>`;
    recentList.innerHTML = issued.map((n) => `<li>#${n}</li>`).join("");
  });
}
