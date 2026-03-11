const API_PREFIX = import.meta.env.VITE_API_PREFIX || "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_PREFIX}${path}`, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "上传请求失败");
  }
  return payload;
}

export function createUploadSession({ accessToken, payload, signal }) {
  return request("/upload/sessions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`
    },
    body: JSON.stringify(payload),
    signal
  });
}

export function uploadChunk({ accessToken, uploadId, chunkIndex, chunkBlob, signal }) {
  const formData = new FormData();
  formData.append("chunk", chunkBlob, `chunk-${chunkIndex}.part`);
  return request(`/upload/sessions/${uploadId}/chunks/${chunkIndex}`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${accessToken}`
    },
    body: formData,
    signal
  });
}

export function completeUploadSession({ accessToken, uploadId, signal }) {
  return request(`/upload/sessions/${uploadId}/complete`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`
    },
    signal
  });
}
