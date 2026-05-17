export const API_BASE_URL = "https://pcu4blgtpf.execute-api.us-east-1.amazonaws.com";

export function buildApiUrl(path) {
  if (!path.startsWith("/")) {
    throw new Error(`API paths must start with '/': ${path}`);
  }

  const normalizedPath = path.replace(/^\/+/, "/");
  return `${API_BASE_URL}${normalizedPath}`;
}
