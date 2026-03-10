const API_PREFIX = import.meta.env.VITE_API_PREFIX || "/api";

export async function fetchAdminLogs({
  accessToken,
  action,
  userId,
  startAt,
  endAt,
  page = 1,
  pageSize = 20
}) {
  const params = new URLSearchParams();
  params.set("page", String(page));
  params.set("page_size", String(pageSize));
  if (action) params.set("action", action);
  if (userId !== null && userId !== undefined && userId !== "") params.set("user_id", String(userId));
  if (startAt) params.set("start_at", startAt);
  if (endAt) params.set("end_at", endAt);

  const response = await fetch(`${API_PREFIX}/admin/logs?${params.toString()}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`
    }
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "获取操作日志失败");
  }
  return payload;
}
