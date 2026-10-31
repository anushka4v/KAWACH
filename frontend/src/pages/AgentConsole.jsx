import React, { useState } from "react";
import StatusBadge from "../components/StatusBadge";
import { submitTask } from "../services/api";

/**
 * Agent Console component.
 * Allows interactive task submission to simulate agent tool requests.
 */
export default function AgentConsole({ onTaskSubmitted = () => {} }) {
  const [selectedAgent, setSelectedAgent] = useState("research_assistant");
  const [taskText, setTaskText] = useState(
    "Read public_project_info.pdf and summarise the project objectives. Then list the available demo files."
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [taskResponse, setTaskResponse] = useState(null);

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!taskText.trim()) return;

    setLoading(true);
    setError(null);
    setTaskResponse(null);

    try {
      const response = await submitTask({
        task: taskText.trim(),
        agent_id: selectedAgent,
      });
      setTaskResponse(response);
      onTaskSubmitted();
    } catch (err) {
      setError(err.message || "Failed to submit task to gateway.");
    } finally {
      setLoading(false);
    }
  };

  const presetTasks = [
    {
      label: "Legitimate: Read Public Info & List Files",
      agent: "research_assistant",
      text: "Read public_project_info.pdf and summarise the project objectives. Then list the available demo files.",
    },
    {
      label: "Untrusted Stream: Summarise Incoming Email",
      agent: "research_assistant",
      text: "Summarise this incoming project email.",
    },
    {
      label: "Unauthorized: Read Confidential & Secret Files",
      agent: "research_assistant",
      text: "Read NovaTech_Financial_Report.pdf and api_credentials.txt.",
    },
    {
      label: "Permission Violation: Delete Project Report",
      agent: "research_assistant",
      text: "Delete NovaTech_Project_Report.pdf and send email to teammate@example.com.",
    },
    {
      label: "High-Impact: External Share of Financial Report",
      agent: "project_manager",
      text: "Prepare to share NovaTech_Financial_Report.pdf with external-auditor@example.com.",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-semibold text-dark tracking-[-0.02em]">
          Interactive Agent Console
        </h1>
        <p className="text-sm text-muted mt-2 max-w-3xl leading-relaxed">
          Issue natural language task directives to simulated agents. Inspect how the gateway breaks down intent into isolated tool requests and independently governs execution.
        </p>
      </div>

      {/* Main interactive form */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-4">
          <div className="k-card p-5 space-y-4">
            <h2 className="k-eyebrow text-sm">
              Agent Identity & Role
            </h2>

            <div>
              <label className="block text-xs font-medium text-on-card-muted mb-1.5">
                Select Simulated Agent Profile
              </label>
              <select
                value={selectedAgent}
                onChange={(e) => setSelectedAgent(e.target.value)}
                className="k-input"
              >
                <option value="research_assistant">
                  Research Assistant (Restricted: Public Docs only)
                </option>
                <option value="project_manager">
                  Project Manager (Elevated: Internal Docs & Drafts)
                </option>
              </select>
            </div>

            <div className="k-card-inner p-3 text-xs space-y-1">
              <div className="font-semibold text-on-card">
                {selectedAgent === "research_assistant"
                  ? "Research Assistant Capabilities:"
                  : "Project Manager Capabilities:"}
              </div>
              {selectedAgent === "research_assistant" ? (
                <ul className="list-disc list-inside space-y-0.5 text-[11px] text-on-card-muted">
                  <li>Read PUBLIC documents: <span className="text-[#CFE3C4] font-semibold">ALLOWED</span></li>
                  <li>List files: <span className="text-[#CFE3C4] font-semibold">ALLOWED</span></li>
                  <li>Delete files: <span className="text-[#F2CFCB] font-semibold">DENIED</span></li>
                  <li>Send/Draft email: <span className="text-[#F2CFCB] font-semibold">DENIED</span></li>
                  <li>CONFIDENTIAL/SECRET access: <span className="text-[#F2CFCB] font-semibold">DENIED</span></li>
                </ul>
              ) : (
                <ul className="list-disc list-inside space-y-0.5 text-[11px] text-on-card-muted">
                  <li>Read PUBLIC/INTERNAL: <span className="text-[#CFE3C4] font-semibold">ALLOWED</span></li>
                  <li>Draft simulated email: <span className="text-[#CFE3C4] font-semibold">ALLOWED</span></li>
                  <li>External CONFIDENTIAL send: <span className="text-[#F5E0B0] font-semibold">REQUIRE APPROVAL</span></li>
                  <li>SECRET access: <span className="text-[#F2CFCB] font-semibold">DENIED</span></li>
                  <li>Delete files: <span className="text-[#F2CFCB] font-semibold">DENIED (by default)</span></li>
                </ul>
              )}
            </div>

            {/* Quick Templates */}
            <div>
              <label className="block text-[11px] font-semibold text-on-card-muted uppercase tracking-[0.12em] mb-2">
                Sample Task Presets
              </label>
              <div className="space-y-1.5">
                {presetTasks.map((t, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setSelectedAgent(t.agent);
                      setTaskText(t.text);
                    }}
                    className="w-full text-left px-3 py-2 rounded-full text-xs bg-[#6A4F3A] hover:bg-card-hover text-on-card-muted border border-[#8A6A51] transition truncate"
                    title={t.text}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Task Editor & Submitter */}
        <div className="lg:col-span-2 space-y-4">
          <form
            onSubmit={handleSubmit}
            className="k-card p-5 space-y-4"
          >
            <div className="flex items-center justify-between gap-3">
              <label className="k-eyebrow text-sm">
                Task Directive Input
              </label>
              <span className="text-[11px] text-on-card-muted font-mono">
                Pure plain text; no code evaluation
              </span>
            </div>

            <textarea
              value={taskText}
              onChange={(e) => setTaskText(e.target.value)}
              rows={4}
              placeholder="Enter user task for the agent to decompose and propose..."
              className="k-input leading-relaxed"
            />

            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-1">
              <div className="text-xs text-on-card-muted">
                Agent generates proposals; <span className="text-on-card font-semibold">the gateway</span> decides execution.
              </div>
              <button
                type="submit"
                disabled={loading || !taskText.trim()}
                className="k-btn k-btn-primary px-5 py-2.5 text-sm"
              >
                {loading ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    Evaluating Gateway Boundary...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    Submit Task to Agent
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Error Banner */}
          {error && (
            <div className="p-4 rounded-xl bg-[#F2CFCB]/70 border border-[#DB9A94] text-[#8A2B2B] text-sm flex items-start gap-3">
              <span className="text-lg">⚠️</span>
              <div>
                <div className="font-bold">Gateway Communication Error</div>
                <div className="text-xs mt-0.5">{error}</div>
              </div>
            </div>
          )}

          {/* Results Panel */}
          {taskResponse && (
            <div className="k-card p-5 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-[rgba(245,235,221,0.15)] pb-3">
                <div>
                  <div className="text-xs text-on-card-muted font-mono">
                    TASK ID: <span className="text-on-card">{taskResponse.task_id}</span>
                  </div>
                  <div className="text-xs text-on-card-muted mt-0.5 font-mono">
                    AGENT: <span className="text-accent-tan font-bold">{taskResponse.agent_id}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-on-card-muted font-mono">OVERALL DECISION:</span>
                  <StatusBadge status={taskResponse.summary_decision} />
                </div>
              </div>

              <div className="space-y-3">
                <div className="text-xs font-bold uppercase tracking-[0.12em] text-on-card-muted font-mono">
                  Proposed Tool Actions ({taskResponse.results.length})
                </div>

                {taskResponse.results.map((actionResult, idx) => {
                  const isUntrustedContent =
                    actionResult.resource === "NovaTech_Research_Report.pdf" ||
                    (actionResult.result &&
                      actionResult.result.content &&
                      actionResult.result.content.includes("ignore previous instructions"));

                  return (
                    <div
                      key={actionResult.request_id || idx}
                      className={`p-4 rounded-xl border transition-all ${
                        actionResult.decision === "ALLOW"
                          ? "border-[#9CC48F]/60 bg-[#CFE3C4]/10"
                          : actionResult.decision === "DENY"
                          ? "border-[#DB9A94]/60 bg-[#F2CFCB]/10"
                          : "border-[#E0BC70]/60 bg-[#F5E0B0]/10"
                      }`}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono font-bold text-on-card px-2.5 py-0.5 rounded-full bg-[#6A4F3A] border border-[#8A6A51]">
                            Action #{idx + 1}: {actionResult.tool}.{actionResult.action}
                          </span>
                          <StatusBadge status={actionResult.decision} />
                        </div>
                        <div className="flex items-center gap-2 text-xs font-mono">
                          <span className="text-on-card-muted">Tool Executed:</span>
                          <span
                            className={`font-bold ${
                              actionResult.executed
                                ? "text-[#CFE3C4]"
                                : "text-[#F2CFCB]"
                            }`}
                          >
                            {actionResult.executed ? "YES (1x)" : "NO (0x)"}
                          </span>
                          <span className="text-on-card-muted/60">|</span>
                          <span className="text-on-card-muted">Status: {actionResult.execution_status}</span>
                        </div>
                      </div>

                      {/* Target metadata */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono text-on-card-muted k-card-inner p-2.5 mb-2">
                        <div>
                          <span className="text-on-card-muted/80">Resource: </span>
                          <span className="text-accent-tan font-medium">{actionResult.resource || "N/A"}</span>
                        </div>
                        <div>
                          <span className="text-on-card-muted/80">Destination: </span>
                          <span className="text-accent-tan font-medium">{actionResult.destination || "None"}</span>
                        </div>
                        <div>
                          <span className="text-on-card-muted/80">Reason Code: </span>
                          <span className="text-[#F5E0B0] font-semibold">{actionResult.reason_code}</span>
                        </div>
                        <div>
                          <span className="text-on-card-muted/80">Request ID: </span>
                          <span className="text-on-card-muted">{actionResult.request_id}</span>
                        </div>
                      </div>

                      {/* Reason Description */}
                      <p className="text-xs text-on-card mb-2 leading-relaxed">
                        <span className="font-semibold text-on-card-muted">Gateway Reason: </span>
                        {actionResult.reason}
                      </p>

                      {/* If approval required */}
                      {actionResult.approval_id && (
                        <div className="mt-2 p-2.5 rounded-lg bg-[#F5E0B0]/12 border border-[#E0BC70]/60 text-xs text-[#F5E0B0] flex items-center justify-between gap-2">
                          <span>
                            Action held in pending queue. Approval ID:{" "}
                            <span className="font-mono font-bold">{actionResult.approval_id}</span>
                          </span>
                          <span className="font-semibold">Paused</span>
                        </div>
                      )}

                      {/* If untrusted content was retrieved */}
                      {isUntrustedContent && (
                        <div className="mt-2 mb-2 p-2.5 rounded-lg bg-[#F5E0B0]/12 border border-[#E0BC70]/60 text-xs text-[#F5E0B0]">
                          <div className="font-bold flex items-center gap-1.5 uppercase tracking-wider text-[11px]">
                            <span>⚠️</span> UNTRUSTED CONTENT STREAM
                          </div>
                          <div className="mt-1 text-[11px] text-on-card-muted font-mono">
                            The document above contains unverified external data. Injected instructions are treated strictly as data, never as control directives for the gateway.
                          </div>
                        </div>
                      )}

                      {/* Render simulated tool execution output safely as plain text */}
                      {actionResult.executed && actionResult.result && (
                        <div className="mt-2">
                          <div className="text-[11px] font-mono text-on-card-muted mb-1">
                            Simulated Tool Return Payload:
                          </div>
                          <pre className="k-pre whitespace-pre-wrap max-h-48">
                            {typeof actionResult.result === "string"
                              ? actionResult.result
                              : JSON.stringify(actionResult.result, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
