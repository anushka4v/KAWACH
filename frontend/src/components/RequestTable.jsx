import React from "react";
import StatusBadge from "./StatusBadge";

/**
 * Reusable Request Table component.
 * Displays requests and gateway decisions on a middle-brown card.
 */
export default function RequestTable({ requests = [], loading = false }) {
  if (loading) {
    return (
      <div className="k-card p-8 text-center text-on-card-muted animate-pulse font-mono text-sm">
        Loading gateway requests...
      </div>
    );
  }

  if (!requests || requests.length === 0) {
    return (
      <div className="k-card p-8 text-center text-on-card-muted font-mono text-sm">
        No requests recorded yet. Run a demo scenario or submit a task to inspect traffic.
      </div>
    );
  }

  const formatTime = (ts) => {
    if (!ts) return "—";
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
    } catch {
      return ts;
    }
  };

  return (
    <div className="k-table-wrap">
      <table className="k-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Agent</th>
            <th>Tool</th>
            <th>Action</th>
            <th>Resource</th>
            <th>Destination</th>
            <th>Decision</th>
            <th>Reason</th>
          </tr>
        </thead>
        <tbody className="font-mono">
          {requests.map((req, idx) => (
            <tr key={req.request_id || req.id || idx}>
              <td className="whitespace-nowrap text-on-card-muted">
                {formatTime(req.created_at || req.timestamp)}
              </td>
              <td className="whitespace-nowrap font-medium text-accent-tan">
                {req.agent_id}
              </td>
              <td className="whitespace-nowrap text-on-card">
                {req.tool}
              </td>
              <td className="whitespace-nowrap">
                <span className="px-2 py-0.5 rounded-full bg-[#6A4F3A] border border-[#8A6A51] text-[11px] text-on-card">
                  {req.action}
                </span>
              </td>
              <td className="max-w-[200px] truncate text-on-card" title={req.resource || "None"}>
                {req.resource || "—"}
              </td>
              <td className="max-w-[150px] truncate text-on-card-muted" title={req.destination || "None"}>
                {req.destination || "—"}
              </td>
              <td className="whitespace-nowrap">
                <StatusBadge status={req.decision} />
              </td>
              <td className="max-w-[260px] truncate text-on-card-muted font-sans text-xs" title={req.reason || ""}>
                {req.reason || "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
