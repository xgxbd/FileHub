const API_PREFIX = import.meta.env.VITE_API_PREFIX || "/api";

export async function fetchHealth() {
  const response = await fetch(`${API_PREFIX}/healthz`, {
    method: "GET",
    headers: {
      Accept: "application/json"
    }
  });

  if (!response.ok) {
    throw new Error(`健康检查失败，状态码: ${response.status}`);
  }

  return response.json();
}
