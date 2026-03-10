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

export async function downloadFile({
  accessToken,
  fileId,
  rangeHeader
}) {
  const headers = {
    Accept: "*/*",
    Authorization: `Bearer ${accessToken}`
  };
  if (rangeHeader) {
    headers.Range = rangeHeader;
  }

  const response = await fetch(`${API_PREFIX}/files/${fileId}/download`, {
    method: "GET",
    headers
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "下载失败");
  }

  return response.blob();
}

export async function previewFile({
  accessToken,
  fileId
}) {
  const response = await fetch(`${API_PREFIX}/files/${fileId}/preview`, {
    method: "GET",
    headers: {
      Accept: "*/*",
      Authorization: `Bearer ${accessToken}`
    }
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "预览失败");
  }

  return {
    blob: await response.blob(),
    contentType: response.headers.get("content-type") || ""
  };
}

export async function softDeleteFile({
  accessToken,
  fileId
}) {
  const response = await fetch(`${API_PREFIX}/files/${fileId}`, {
    method: "DELETE",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`
    }
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "删除失败");
  }
  return payload;
}

export async function fetchRecycleFileList({
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

  const response = await fetch(`${API_PREFIX}/recycle/files?${params.toString()}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`
    }
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "获取回收站列表失败");
  }
  return payload;
}

export async function restoreRecycleFile({
  accessToken,
  fileId
}) {
  const response = await fetch(`${API_PREFIX}/recycle/files/${fileId}/restore`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`
    }
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "恢复失败");
  }
  return payload;
}

export async function purgeRecycleFile({
  accessToken,
  fileId
}) {
  const response = await fetch(`${API_PREFIX}/recycle/files/${fileId}/purge`, {
    method: "DELETE",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`
    }
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "彻底删除失败");
  }
  return payload;
}
