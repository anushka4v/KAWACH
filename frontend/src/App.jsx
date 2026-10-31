import React, { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import AgentConsole from "./pages/AgentConsole";
import Approvals from "./pages/Approvals";
import AuditLogs from "./pages/AuditLogs";
import DemoScenarios from "./pages/DemoScenarios";
import { getApprovals } from "./services/api";

const PAGE_TITLES = {
  dashboard: "Dashboard",
  agent_console: "Agent Console",
  approvals: "Approvals",
  audit_logs: "Audit Logs",
  demo_scenarios: "Demo Scenarios",
};

export default function App() {
  const [currentPage, setCurrentPage] = useState("dashboard");
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const fetchPendingCount = async () => {
    try {
      const pending = await getApprovals("PENDING");
      setPendingApprovalsCount((pending || []).length);
    } catch {
      // Backend may be offline or initializing
    }
  };

  useEffect(() => {
    fetchPendingCount();

    // Refresh pending approvals every 10 seconds
    const interval = setInterval(() => {
      fetchPendingCount();
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const refreshState = () => {
    fetchPendingCount();
  };

  return (
    <div className="min-h-screen text-dark flex">
      {/* Sidebar */}
      <Sidebar
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        pendingApprovalsCount={pendingApprovalsCount}
        isOpen={sidebarOpen}
        setIsOpen={setSidebarOpen}
      />

      {/* Main content wrapper */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-64">
        {/* Top Header Bar */}
        <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-4 sm:px-6 bg-sidebar/90 border-b border-line backdrop-blur">
          <div className="flex items-center gap-3">
            {/* Mobile hamburger */}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-full text-dark hover:bg-[#D9C7AE] lg:hidden focus:outline-none transition"
              aria-label="Toggle Navigation"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>

            <span className="text-sm font-semibold text-dark tracking-tight">
              {PAGE_TITLES[currentPage] || "Dashboard"}
            </span>
          </div>

          {/* Right Header Bar: keep pending actions pill if active */}
          <div className="flex items-center gap-3">
            {pendingApprovalsCount > 0 && (
              <button
                onClick={() => setCurrentPage("approvals")}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition hover:brightness-[0.98]"
                style={{
                  color: "#8A5A12",
                  backgroundColor: "#F5E0B0",
                  border: "1px solid #E0BC70",
                }}
              >
                <span>⏳</span>
                <span>{pendingApprovalsCount} Action{pendingApprovalsCount > 1 ? "s" : ""} Pending</span>
              </button>
            )}
          </div>
        </header>

        {/* Dynamic Page Content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {currentPage === "dashboard" && (
            <Dashboard setCurrentPage={setCurrentPage} />
          )}
          {currentPage === "agent_console" && (
            <AgentConsole onTaskSubmitted={refreshState} />
          )}
          {currentPage === "approvals" && (
            <Approvals onApprovalUpdated={refreshState} />
          )}
          {currentPage === "audit_logs" && <AuditLogs />}
          {currentPage === "demo_scenarios" && (
            <DemoScenarios onDemoExecuted={refreshState} />
          )}
        </main>
      </div>
    </div>
  );
}
