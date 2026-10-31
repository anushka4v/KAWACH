/**
 * Centralized API service for KAWACH / AGENTSHIELD.
 * Communicates with FastAPI backend on http://127.0.0.1:8000 (http://localhost:8000).
 * Never decides security policies on the frontend.
 */

   const API_BASE = (import.meta.env.VITE_API_BASE || "http://localhost:8000").replace(/\/$/, "");

async function request(path, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const errorMsg =
        data.detail || `Request failed with HTTP status ${response.status}`;
      throw new Error(errorMsg);
    }

    return data;
  } catch (err) {
    if (
      err.name === "TypeError" &&
      (err.message.includes("fetch") || err.message.includes("Failed to fetch"))
    ) {
      throw new Error(
        "Backend unreachable. Please ensure the Python FastAPI server is running at http://localhost:8000."
      );
    }
    throw err;
  }
}

export const getHealth = () => request("/api/health");

export const submitTask = (payload) =>
  request("/api/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const getRequests = (limit = 100) =>
  request(`/api/requests?limit=${limit}`);

export const getApprovals = (status = "PENDING") =>
  request(`/api/approvals?status=${encodeURIComponent(status)}`);

export const approveRequest = (id) =>
  request(`/api/approvals/${encodeURIComponent(id)}/approve`, {
    method: "POST",
  });

export const rejectRequest = (id) =>
  request(`/api/approvals/${encodeURIComponent(id)}/reject`, {
    method: "POST",
  });

export const getAuditLogs = (limit = 100, decision = null) => {
  const query = decision
    ? `?limit=${limit}&decision=${encodeURIComponent(decision)}`
    : `?limit=${limit}`;
  return request(`/api/audit-logs${query}`);
};

export const getState = () => request("/api/state");

export const resetDemo = () =>
  request("/api/demo/reset", {
    method: "POST",
  });
