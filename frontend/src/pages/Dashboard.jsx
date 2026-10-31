import React, { useState, useEffect } from "react";
import StatCard from "../components/StatCard";
import RequestTable from "../components/RequestTable";
import { getRequests, getApprovals } from "../services/api";

/**
 * Dashboard page component.
 * Displays key security metrics, recent gateway traffic, and system overview.
 */
export default function Dashboard({ setCurrentPage }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [requests, setRequests] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    allowed: 0,
    denied: 0,
    pending: 0,
  });
  const [isSampleData, setIsSampleData] = useState(false);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [reqData, pendingData] = await Promise.all([
        getRequests(50),
        getApprovals("PENDING"),
      ]);

      const reqList = reqData || [];
      const pendingList = pendingData || [];

      const allowedCount = reqList.filter((r) => r.decision === "ALLOW").length;
      const deniedCount = reqList.filter((r) => r.decision === "DENY").length;

      setRequests(reqList);
      setStats({
        total: reqList.length,
        allowed: allowedCount,
        denied: deniedCount,
        pending: pendingList.length,
      });
      setIsSampleData(false);
    } catch (err) {
      console.warn("Could not fetch live dashboard metrics:", err);
      setError(err.message);
      // Fallback sample data strictly labeled as SAMPLE DATA
      setIsSampleData(true);
      setRequests([
        {
          request_id: "sample_001",
          agent_id: "research_assistant",
          tool: "document_reader",
          action: "read",
          resource: "public_project_info.pdf",
          destination: null,
          decision: "ALLOW",
          reason: "Public project overview allowed for research assistant.",
          created_at: new Date().toISOString(),
        },
        {
          request_id: "sample_002",
          agent_id: "research_assistant",
          tool: "email_sender",
          action: "send",
          resource: "api_credentials.txt",
          destination: "attacker@example.com",
          decision: "DENY",
          reason: "Agent lacks permission to invoke email_sender.",
          created_at: new Date(Date.now() - 30000).toISOString(),
        },
      ]);
      setStats({
        total: 2,
        allowed: 1,
        denied: 1,
        pending: 0,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-dark tracking-[-0.02em]">
            Gateway Telemetry & Policy Metrics
          </h1>
          <p className="text-sm text-muted mt-2 max-w-2xl leading-relaxed">
            Real-time inspection of agent-to-tool boundaries and authorization decisions.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchDashboardData}
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
          <button
            onClick={() => setCurrentPage("demo_scenarios")}
            className="k-btn k-btn-primary"
          >
            Launch Demos
          </button>
        </div>
      </div>

      {/* Offline / Sample Data Notice Banner */}
      {isSampleData && (
        <div className="p-3.5 rounded-xl bg-[#F5E0B0]/60 border border-[#E0BC70] text-[#8A5A12] text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded-full bg-[#F5E0B0] text-[#8A5A12] font-bold uppercase tracking-wider text-[10px] border border-[#E0BC70]">
              SAMPLE DATA
            </span>
            <span>
              Backend is unreachable ({error}). Showing placeholder layout data. Once connected, live gateway telemetry replaces this view.
            </span>
          </div>
        </div>
      )}

      {/* Metric Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Tool Invocations"
          value={stats.total}
          subtext="Through the security gateway"
          icon="🛡️"
        />
        <StatCard
          title="Permitted Actions"
          value={stats.allowed}
          subtext="Verified role & resource policy"
          icon="✅"
        />
        <StatCard
          title="Blocked Violations"
          value={stats.denied}
          subtext="Zero tool execution occurred"
          icon="🚫"
        />
        <StatCard
          title="Pending Human Approvals"
          value={stats.pending}
          subtext="High-impact actions paused"
          icon="⏳"
        />
      </div>

      {/* Architecture Highlights & Invariant Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="k-card p-5">
          <div className="k-eyebrow text-[11px] mb-2">
            01 • The Agent Proposes
          </div>
          <p className="text-xs text-on-card-muted leading-relaxed">
            AI agents only submit structured intents (tool + action + resource + destination). Agents have zero direct route to OS, shell, network, or tools.
          </p>
        </div>
        <div className="k-card p-5">
          <div className="k-eyebrow text-[11px] mb-2">
            02 • The Gateway Decides
          </div>
          <p className="text-xs text-on-card-muted leading-relaxed">
            The gateway evaluates deterministic role allow-lists and resource sensitivity tiers. DENY and REQUIRE_APPROVAL never trigger tool functions.
          </p>
        </div>
        <div className="k-card p-5">
          <div className="k-eyebrow text-[11px] mb-2">
            03 • Tamper-Proof Audit
          </div>
          <p className="text-xs text-on-card-muted leading-relaxed">
            Every request, decision reason, SHA-256 payload binding, and tool execution status is written immutably into SQLite audit trails.
          </p>
        </div>
      </div>

      {/* Recent Requests Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-dark tracking-tight">
            Recent Tool Requests & Authorizations
          </h2>
          <span className="text-xs text-muted font-mono">
            Showing latest {requests.length} events
          </span>
        </div>
        <RequestTable requests={requests} loading={loading} />
      </div>
    </div>
  );
}
