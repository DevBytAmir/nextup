requireAuth("number", initNumberPage);

function initNumberPage() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="page number-page">
      <h1>Issue Number</h1>
      <button id="issue-btn">Issue Next Number</button>
      <div id="last-issued"></div>
      <ul id="recent-list"></ul>
    </div>
  `;
  const recentList = document.getElementById("recent-list");
  const lastIssued = document.getElementById("last-issued");
  const issued = [];

  document.getElementById("issue-btn").addEventListener("click", async () => {
    const res = await apiPost("/api/number/issue", "number");
    if (!res.ok) return;
    const ticket = await res.json();
    issued.unshift(ticket.number);
    issued.length = Math.min(issued.length, 5);
    lastIssued.textContent = `Last issued: #${ticket.number}`;
    recentList.innerHTML = issued.map((n) => `<li>#${n}</li>`).join("");
  });
}
