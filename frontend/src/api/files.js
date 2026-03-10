const API_PREFIX = import.meta.env.VITE_API_PREFIX || "/api";

export async function fetchFileList({
  accessToken,
  keyword,
  minSize,
  maxSize,
  page = 1,
  pageSize = 20
}) {
  const params = new URLSearchParams();
  params.set("page", String(page));
  params.set("page_size", String(pageSize));

  if (keyword) params.set("keyword", keyword);
  if (minSize !== null && minSize !== undefined && minSize !== "") params.set("min_size", String(minSize));
  if (maxSize !== null && maxSize !== undefined && maxSize !== "") params.set("max_size", String(maxSize));

  const response = await fetch(`${API_PREFIX}/files?${params.toString()}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`
    }
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "获取文件列表失败");
  }
  return payload;
}
