const API_PREFIX = import.meta.env.VITE_API_PREFIX || "/api";

export async function fetchFileList({
  accessToken,
  keyword,
  directory,
  sortBy,
  page = 1,
  pageSize = 20
}) {
  const params = new URLSearchParams();
  params.set("page", String(page));
  params.set("page_size", String(pageSize));

  if (keyword) params.set("keyword", keyword);
  if (directory) params.set("directory", directory);
  if (sortBy) params.set("sort_by", sortBy);

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

export async function fetchFolderTree({ accessToken }) {
  const response = await fetch(`${API_PREFIX}/folders/tree`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`
    }
  });

  const payload = await response.json().catch(() => []);
  if (!response.ok) {
    throw new Error(payload.detail || "获取目录树失败");
  }
  return Array.isArray(payload) ? payload : [];
}

export async function createFolder({
  accessToken,
  parentDirectory,
  folderName
}) {
  const response = await fetch(`${API_PREFIX}/folders`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`
    },
    body: JSON.stringify({
      parent_directory: parentDirectory,
      folder_name: folderName
    })
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "创建文件夹失败");
  }
  return payload;
}

export async function renameFolder({
  accessToken,
  path,
  newName
}) {
  const response = await fetch(`${API_PREFIX}/folders/rename`, {
    method: "PATCH",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`
    },
    body: JSON.stringify({
      path,
      new_name: newName
    })
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "重命名文件夹失败");
  }
  return payload;
}

export async function deleteFolder({
  accessToken,
  path,
  recursive = false
}) {
  const params = new URLSearchParams();
  params.set("path", path);
  params.set("recursive", String(Boolean(recursive)));

  const response = await fetch(`${API_PREFIX}/folders?${params.toString()}`, {
    method: "DELETE",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`
    }
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "删除文件夹失败");
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
    const payload = await response.json().catch(async () => {
      const text = await response.text().catch(() => "");
      return { detail: text };
    });
    throw new Error(payload.detail || `下载失败（HTTP ${response.status}）`);
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

export async function fetchRecycleFolderList({ accessToken }) {
  const response = await fetch(`${API_PREFIX}/recycle/folders`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`
    }
  });

  const payload = await response.json().catch(() => []);
  if (!response.ok) {
    throw new Error(payload.detail || "获取文件夹回收站失败");
  }
  return Array.isArray(payload) ? payload : [];
}

export async function restoreRecycleFolder({
  accessToken,
  path
}) {
  const params = new URLSearchParams();
  params.set("path", path);

  const response = await fetch(`${API_PREFIX}/recycle/folders/restore?${params.toString()}`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`
    }
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "恢复文件夹失败");
  }
  return payload;
}

export async function purgeRecycleFolder({
  accessToken,
  path
}) {
  const params = new URLSearchParams();
  params.set("path", path);

  const response = await fetch(`${API_PREFIX}/recycle/folders/purge?${params.toString()}`, {
    method: "DELETE",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`
    }
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "彻底删除文件夹失败");
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
