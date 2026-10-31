import React, { useState, useEffect } from "react";
import StatusBadge from "../components/StatusBadge";
import { getApprovals, approveRequest, rejectRequest } from "../services/api";

/**
 * Human Approval Queue component.
 * Allows human-in-the-loop operators to authorize or deny paused high-impact actions.
 */
export default function Approvals({ onApprovalUpdated = () => {} }) {
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [historyApprovals, setHistoryApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState(null);
  const [actionFeedback, setActionFeedback] = useState(null);
  const [error, setError] = useState(null);

  const fetchApprovals = async () => {
    setLoading(true);
    setError(null);
    try {
      const [pendingList, allList] = await Promise.all([
        getApprovals("PENDING"),
        getApprovals("ALL"),
      ]);

      setPendingApprovals(pendingList || []);
      const decided = (allList || []).filter((a) => a.status !== "PENDING");
      setHistoryApprovals(decided);
    } catch (err) {
      setError(err.message || "Failed to load approval records.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
  }, []);

  const handleApprove = async (id) => {
    setProcessingId(id);
    setActionFeedback(null);
    try {
      const res = await approveRequest(id);
      setActionFeedback({
        type: "success",
        text: `APPROVED: Executed stored payload once through gateway. ${res.message || ""}`,
      });
      await fetchApprovals();
      onApprovalUpdated();
    } catch (err) {
      setActionFeedback({
        type: "error",
        text: `Approval failed: ${err.message}`,
      });
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (id) => {
    setProcessingId(id);
    setActionFeedback(null);
    try {
      await rejectRequest(id);
      setActionFeedback({
        type: "neutral",
        text: `REJECTED: Request declined. Zero tools executed. State remained unchanged.`,
      });
      await fetchApprovals();
      onApprovalUpdated();
    } catch (err) {
      setActionFeedback({
        type: "error",
        text: `Rejection failed: ${err.message}`,
      });
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-dark tracking-[-0.02em]">
            Human-in-the-Loop Approval Queue
          </h1>
          <p className="text-sm text-muted mt-2 max-w-2xl leading-relaxed">
            Deterministic pause-points for high-impact tool invocations. Bound to immutable SHA-256 payload snapshots.
          </p>
        </div>
        <button
          onClick={fetchApprovals}
          disabled={loading}
          className="k-btn k-btn-secondary self-start"
        >
          <svg
            className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh Queue
        </button>
      </div>

      {/* Feedback Banner */}
      {actionFeedback && (
        <div
          className={`p-4 rounded-xl border text-sm font-medium flex items-center justify-between gap-3 ${
            actionFeedback.type === "success"
              ? "bg-[#CFE3C4] border-[#9CC48F] text-[#2F5A2A]"
              : actionFeedback.type === "error"
              ? "bg-[#F2CFCB] border-[#DB9A94] text-[#8A2B2B]"
              : "bg-[#E5D9C6] border-[#C9B396] text-[#6E5645]"
          }`}
        >
          <div className="flex items-center gap-2">
            <span>
              {actionFeedback.type === "success"
                ? "✅"
                : actionFeedback.type === "error"
                ? "❌"
                : "🚫"}
            </span>
            <span>{actionFeedback.text}</span>
          </div>
          <button
            onClick={() => setActionFeedback(null)}
            className="text-xs opacity-70 hover:opacity-100 ml-4 font-mono"
          >
            DISMISS
          </button>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-[#F2CFCB]/70 border border-[#DB9A94] text-[#8A2B2B] text-sm">
          {error}
        </div>
      )}

      {/* Pending Approvals Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-dark tracking-tight flex items-center gap-2">
            Pending Human Authorizations
            <span
              className="px-2 py-0.5 rounded-full text-xs font-mono font-semibold"
              style={{ color: "#8A5A12", backgroundColor: "#F5E0B0", border: "1px solid #E0BC70" }}
            >
              {pendingApprovals.length}
            </span>
          </h2>
          <span className="text-xs text-muted font-mono">
            One-time execution guarantee
          </span>
        </div>

        {loading ? (
          <div className="k-card p-8 text-center text-on-card-muted font-mono text-sm animate-pulse">
            Loading pending approvals...
          </div>
        ) : pendingApprovals.length === 0 ? (
          <div className="k-card p-8 text-center text-on-card-muted font-mono text-sm">
            No approvals pending. High-impact operations (such as external confidential sharing) will pause here.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {pendingApprovals.map((appr) => (
              <div
                key={appr.approval_id}
                className="k-card p-5 space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-[rgba(245,235,221,0.15)] pb-3">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-accent-tan">
                      ID: {appr.approval_id}
                    </span>
                    <StatusBadge status="PENDING" />
                  </div>
                  <div className="text-xs text-on-card-muted font-mono">
                    Created: {new Date(appr.created_at).toLocaleString()}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                  <div className="space-y-1.5 p-3 k-card-inner">
                    <div>
                      <span className="text-on-card-muted/80">Proposing Agent: </span>
                      <span className="text-accent-tan font-bold">{appr.agent_id}</span>
                    </div>
                    <div>
                      <span className="text-on-card-muted/80">Target Tool: </span>
                      <span className="text-on-card">{appr.tool}</span>
                    </div>
                    <div>
                      <span className="text-on-card-muted/80">Action: </span>
                      <span className="text-on-card font-bold">{appr.action}</span>
                    </div>
                    <div>
                      <span className="text-on-card-muted/80">Target Resource: </span>
                      <span className="text-[#F5E0B0] font-semibold">{appr.resource || "None"}</span>
                    </div>
                    <div>
                      <span className="text-on-card-muted/80">Destination: </span>
                      <span className="text-[#F5E0B0] font-semibold">{appr.destination || "None"}</span>
                    </div>
                  </div>

                  <div className="space-y-2 p-3 k-card-inner flex flex-col justify-between">
                    <div>
                      <div className="text-on-card-muted font-sans text-xs">
                        <span className="font-semibold text-on-card">Policy Trigger: </span>
                        {appr.reason}
                      </div>
                      <div className="mt-2 text-[10px] text-on-card-muted/70 break-all">
                        <span className="text-on-card-muted font-semibold">SHA-256 Hash Binding: </span>
                        <span className="text-accent-tan">{appr.payload_hash}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Stored Payload Snapshot Details */}
                <div className="text-xs">
                  <div className="text-[11px] font-mono text-on-card-muted mb-1">
                    Immutable Original Payload Snapshot:
                  </div>
                  <pre className="k-pre max-h-32">
                    {JSON.stringify(appr.payload_snapshot, null, 2)}
                  </pre>
                </div>

                {/* Approve / Reject Controls */}
                <div className="flex flex-wrap items-center justify-end gap-3 pt-2">
                  <button
                    onClick={() => handleReject(appr.approval_id)}
                    disabled={processingId === appr.approval_id}
                    className="k-btn k-btn-danger-light px-4 py-2"
                  >
                    {processingId === appr.approval_id ? "Processing..." : "Reject Action (No Execution)"}
                  </button>
                  <button
                    onClick={() => handleApprove(appr.approval_id)}
                    disabled={processingId === appr.approval_id}
                    className="k-btn k-btn-primary px-5 py-2"
                  >
                    {processingId === appr.approval_id ? "Executing Stored Payload..." : "Approve & Execute Exact Action"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Decided Approvals History */}
      <div className="space-y-3 pt-6 border-t border-line">
        <h2 className="text-lg font-semibold text-dark tracking-tight">
          Resolved Approval History
        </h2>
        {historyApprovals.length === 0 ? (
          <div className="k-card p-6 text-center text-on-card-muted font-mono text-xs">
            No previously resolved approvals in session.
          </div>
        ) : (
          <div className="k-table-wrap">
            <table className="k-table">
              <thead>
                <tr>
                  <th>Approval ID</th>
                  <th>Agent</th>
                  <th>Tool/Action</th>
                  <th>Resource</th>
                  <th>Destination</th>
                  <th>Outcome</th>
                  <th>Approver</th>
                  <th>Decided At</th>
                </tr>
              </thead>
              <tbody className="font-mono">
                {historyApprovals.map((h) => (
                  <tr key={h.approval_id}>
                    <td className="text-on-card-muted">{h.approval_id}</td>
                    <td className="text-accent-tan">{h.agent_id}</td>
                    <td className="text-on-card">{h.tool}.{h.action}</td>
                    <td className="text-on-card">{h.resource || "—"}</td>
                    <td className="text-on-card-muted">{h.destination || "—"}</td>
                    <td>
                      <StatusBadge status={h.status} />
                    </td>
                    <td className="text-on-card-muted">{h.approver || "System"}</td>
                    <td className="text-on-card-muted">
                      {h.decided_at ? new Date(h.decided_at).toLocaleTimeString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
