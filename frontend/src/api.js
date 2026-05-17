import { buildApiUrl } from "./api/baseUrl.js";

export async function apiGet(path) {
  const res = await fetch(buildApiUrl(path));
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

export async function apiPost(path, body) {
  const res = await fetch(buildApiUrl(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    let detail = "";
    try {
      const data = await res.json();
      detail = data.detail ? ` - ${data.detail}` : "";
    } catch {}
    throw new Error(`POST ${path} failed: ${res.status}${detail}`);
  }

  return res.json();
}
