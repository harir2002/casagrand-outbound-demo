/**
 * Low-level HTTP helper for local backend integration.
 * Prefer empty VITE_API_BASE with Vite proxy, or set an absolute URL.
 */

const API_BASE = import.meta.env.VITE_API_BASE || "";

export class ApiError extends Error {
  constructor(message, { status, latencyMs, body } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.latencyMs = latencyMs;
    this.body = body;
  }
}

export async function request(path, options = {}) {
  const started = performance.now();
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });
  } catch (err) {
    const latencyMs = Math.round(performance.now() - started);
    throw new ApiError(err.message || "Network error — is the backend running?", {
      latencyMs,
    });
  }

  const latencyMs = Math.round(performance.now() - started);
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = data.detail || data.error || response.statusText || "Request failed";
    throw new ApiError(typeof detail === "string" ? detail : JSON.stringify(detail), {
      status: response.status,
      latencyMs,
      body: data,
    });
  }

  return { data, latencyMs };
}
