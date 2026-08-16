const TOKEN_KEY_PREFIX = "queue_token_";

function getToken(page) {
  return localStorage.getItem(TOKEN_KEY_PREFIX + page);
}

function setToken(page, token) {
  localStorage.setItem(TOKEN_KEY_PREFIX + page, token);
}

function clearToken(page) {
  localStorage.removeItem(TOKEN_KEY_PREFIX + page);
}

async function login(page, pin) {
  const res = await fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ page, pin }),
  });
  if (!res.ok) return false;
  const data = await res.json();
  setToken(page, data.token);
  return true;
}

async function apiPost(path, page, body) {
  const token = getToken(page);
  const res = await fetch(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body || {}),
  });
  if (res.status === 401) {
    clearToken(page);
    location.reload();
  }
  return res;
}

async function apiGet(path) {
  return fetch(path);
}
