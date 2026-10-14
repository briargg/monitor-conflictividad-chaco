// frontend/src/api.js
const API_URL = import.meta.env.DEV
  ? "http://localhost:8000"
  : "https://monitor-conflictividad-chaco.onrender.com";

export async function apiFetch(path, options = {}) {
  const token = localStorage.getItem("token");
  const headers = { ...(options.headers || {}) };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  return res;
}

export { API_URL };