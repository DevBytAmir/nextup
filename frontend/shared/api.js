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

async function login(page, pin, counter) {
  const res = await fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ page, pin, counter }),
  });
  if (!res.ok) return false;
  const data = await res.json();
  setToken(page, data.token);
  return true;
}

async function logout(page) {
  const token = getToken(page);
  clearToken(page);
  if (token) {
    await fetch("/api/logout", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    }).catch(() => {});
  }
}

async function authedFetch(path, page, options = {}) {
  const token = getToken(page);
  const res = await fetch(path, {
    ...options,
    headers: { ...options.headers, Authorization: `Bearer ${token}` },
  });
  if (res.status === 401) {
    clearToken(page);
    location.reload();
  }
  return res;
}

async function apiPost(path, page, body) {
  return authedFetch(path, page, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
}

async function apiGet(path) {
  return fetch(path);
}

async function apiGetAuthed(path, page) {
  return authedFetch(path, page);
}
