const API_PREFIX = import.meta.env.VITE_API_PREFIX || "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_PREFIX}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(options.headers || {})
    }
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "请求失败");
  }

  return payload;
}

export function register(payload) {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function login(payload) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function refresh(payload) {
  return request("/auth/refresh", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function fetchCurrentUser(accessToken) {
  return request("/auth/me", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`
    }
  });
}
