import { buildApiUrl } from "./api/baseUrl.js";

export async function apiRequest(path, options = {}) {
  const { headers, body, ...rest } = options;
  const requestHeaders = { ...(headers || {}) };

  const response = await fetch(buildApiUrl(path), {
    credentials: "include",
    headers: requestHeaders,
    body,
    ...rest,
  });

  if (!response.ok) {
    let detail = "";
    try {
      const data = await response.json();
      detail = data.detail || data.message || "";
    } catch {
      detail = "";
    }
    throw new Error(detail || `${rest.method || "GET"} ${path} failed: ${response.status}`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export async function apiGet(path, options = {}) {
  return apiRequest(path, { ...options, method: "GET" });
}

export async function apiPost(path, payload, options = {}) {
  return apiRequest(path, {
    ...options,
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    body: JSON.stringify(payload),
  });
}

export async function apiPatch(path, payload, options = {}) {
  return apiRequest(path, {
    ...options,
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    body: JSON.stringify(payload),
  });
}
