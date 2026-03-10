const ACCESS_TOKEN_KEY = "filehub_access_token";
const REFRESH_TOKEN_KEY = "filehub_refresh_token";

export function saveTokens({ accessToken, refreshToken }) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken || "");
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken || "");
}

export function readTokens() {
  const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY) || "";
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY) || "";
  return { accessToken, refreshToken };
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}
