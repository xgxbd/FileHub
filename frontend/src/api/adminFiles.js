const API_PREFIX = import.meta.env.VITE_API_PREFIX || "/api";

export async function fetchAdminFiles({
  accessToken,
  keyword,
  ownerId,
  status = "active",
  sortBy,
  page = 1,
  pageSize = 20
}) {
  const params = new URLSearchParams();
  params.set("page", String(page));
  params.set("page_size", String(pageSize));
  params.set("status", status);

  if (keyword) params.set("keyword", keyword);
  if (ownerId !== null && ownerId !== undefined && ownerId !== "") params.set("owner_id", String(ownerId));
  if (sortBy) params.set("sort_by", sortBy);

  const response = await fetch(`${API_PREFIX}/admin/files?${params.toString()}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`
    }
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "获取管理员文件列表失败");
  }
  return payload;
}
