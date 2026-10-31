import React, { useState, useEffect } from "react";
import StatusBadge from "../components/StatusBadge";
import { getAuditLogs } from "../services/api";

/**
 * Audit Logs page component.
 * Provides complete chronological audit trail of all security decisions and execution evidence.
 */
export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [decisionFilter, setDecisionFilter] = useState("ALL");
  const [error, setError] = useState(null);

  const fetchLogs = async (filter = decisionFilter) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAuditLogs(200, filter === "ALL" ? null : filter);
      setLogs(data || []);
    } catch (err) {
      setError(err.message || "Failed to retrieve audit log trail.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs(decisionFilter);
  }, [decisionFilter]);

  const formatTimestamp = (ts) => {
    if (!ts) return "—";
    try {
      const d = new Date(ts);
      return d.toLocaleString([], {
        hour12: false,
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    } catch {
      return ts;
    }
  };

  return (
    <div className="space-y-8">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-dark tracking-[-0.02em]">
            Security Audit Trail & Evidence Log
          </h1>
          <p className="text-sm text-muted mt-2 max-w-2xl leading-relaxed">
            Tamper-evident record of all tool requests, authorization decisions, human interventions, and execution outcomes.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Decision Filter */}
          <div className="flex items-center gap-1 bg-input border border-line rounded-full p-1 text-xs">
            {["ALL", "ALLOW", "DENY", "REQUIRE_APPROVAL"].map((f) => (
              <button
                key={f}
                onClick={() => setDecisionFilter(f)}
                className={`px-3 py-1 rounded-full font-medium transition ${
                  decisionFilter === f
                    ? "bg-accent-dark text-on-card font-bold"
                    : "text-muted hover:bg-[#D9C7AE] hover:text-dark"
                }`}
              >
                {f === "REQUIRE_APPROVAL" ? "APPROVAL" : f}
              </button>
            ))}
          </div>

          <button
            onClick={() => fetchLogs()}
            disabled={loading}
            className="k-btn k-btn-secondary"
          >
            <svg
              className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 rounded-xl bg-[#F2CFCB]/70 border border-[#DB9A94] text-[#8A2B2B] text-sm">
          {error}
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className="k-card p-12 text-center text-on-card-muted font-mono text-sm animate-pulse">
          Retrieving audit records from SQLite engine...
        </div>
      ) : logs.length === 0 ? (
        <div className="k-card p-12 text-center text-on-card-muted font-mono text-sm">
          No audit records found matching the current filter.
        </div>
      ) : (
        <div className="k-table-wrap">
          <table className="k-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Req ID</th>
                <th>Agent</th>
                <th>Tool / Action</th>
                <th>Resource Target</th>
                <th>Destination</th>
                <th>Gateway Decision</th>
                <th>Execution Status</th>
                <th>Policy Reason Code</th>
                <th>Inspectable Reason</th>
              </tr>
            </thead>
            <tbody className="font-mono">
              {logs.map((log) => (
                <tr key={log.id}>
                  <td className="whitespace-nowrap text-on-card-muted text-[11px]">
                    {formatTimestamp(log.timestamp)}
                  </td>
                  <td className="whitespace-nowrap text-accent-tan font-semibold">
                    {log.request_id}
                  </td>
                  <td className="whitespace-nowrap text-on-card font-medium">
                    {log.agent_id}
                  </td>
                  <td className="whitespace-nowrap">
                    <span className="text-on-card">{log.tool}</span>
                    <span className="text-on-card-muted/60">.</span>
                    <span className="text-accent-tan font-semibold">{log.action}</span>
                  </td>
                  <td
                    className="max-w-[180px] truncate text-on-card"
                    title={log.resource || "N/A"}
                  >
                    {log.resource || "—"}
                  </td>
                  <td
                    className="max-w-[140px] truncate text-on-card-muted"
                    title={log.destination || "None"}
                  >
                    {log.destination || "—"}
                  </td>
                  <td className="whitespace-nowrap">
                    <StatusBadge status={log.decision} />
                  </td>
                  <td className="whitespace-nowrap">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                        log.execution_status === "EXECUTED"
                          ? "bg-[#CFE3C4] text-[#2F5A2A] border-[#9CC48F]"
                          : log.execution_status === "PENDING_APPROVAL"
                          ? "bg-[#F5E0B0] text-[#8A5A12] border-[#E0BC70]"
                          : log.execution_status === "FAILED"
                          ? "bg-[#F2CFCB] text-[#8A2B2B] border-[#DB9A94]"
                          : "bg-[#E5D9C6] text-[#6E5645] border-[#C9B396]"
                      }`}
                    >
                      {log.execution_status}
                    </span>
                  </td>
                  <td className="whitespace-nowrap text-[11px] text-[#F5E0B0]">
                    {log.reason_code}
                  </td>
                  <td
                    className="max-w-[280px] truncate font-sans text-xs text-on-card-muted"
                    title={log.reason}
                  >
                    {log.reason}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
