import React from "react";
import logoImg from "../assets/kawach-logo-brown-trimmed.png";

/**
 * Sidebar navigation component.
 * Warm beige gallery theme with a dark-brown active pill.
 */
export default function Sidebar({
  currentPage,
  setCurrentPage,
  pendingApprovalsCount = 0,
  isOpen = true,
  setIsOpen = () => {},
}) {
  const navItems = [
    {
      id: "dashboard",
      label: "Dashboard",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
        </svg>
      ),
    },
    {
      id: "agent_console",
      label: "Agent Console",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      ),
    },
    {
      id: "approvals",
      label: "Approvals",
      badge: pendingApprovalsCount,
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
    },
    {
      id: "audit_logs",
      label: "Audit Logs",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
        </svg>
      ),
    },
    {
      id: "demo_scenarios",
      label: "Demo Scenarios",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-[#3B2A20]/35 backdrop-blur-sm lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 flex flex-col w-64 bg-sidebar border-r border-line transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Brand — logo only, no wordmark text. min-h keeps the header block
            the same height so the PS-01 box and nav do not shift. */}
        <div className="flex items-center justify-center min-h-[194px] px-4 py-4 border-b border-line">
          <img
            src={logoImg}
            alt="KAWACH Shield Logo"
            className="w-full max-w-[230px] h-auto object-contain"
          />
        </div>

        {/* Problem Statement Pill */}
        <div className="mx-4 my-4 px-4 py-3 rounded-xl k-card">
          <div className="k-eyebrow text-[10px] mb-1">PS-01 Track</div>
          <div className="text-[11px] text-on-card leading-relaxed">
            Secure the Agent, Not Just the Prompt
          </div>
        </div>

        {/* Navigation items */}
        <nav className="flex-1 px-3 py-2 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setCurrentPage(item.id);
                  if (window.innerWidth < 1024) setIsOpen(false);
                }}
                className={`w-full flex items-center justify-between px-4 py-2.5 rounded-full text-sm font-medium transition-all ${
                  isActive
                    ? "bg-accent-dark text-on-card shadow-[0_6px_16px_rgba(59,42,32,0.22)]"
                    : "text-dark hover:bg-[#D9C7AE]"
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className={isActive ? "text-accent-tan" : "text-dark"}>
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                </div>

                {item.badge > 0 && (
                  <span
                    className="px-2 py-0.5 text-xs font-bold rounded-full"
                    style={{
                      color: "#8A5A12",
                      backgroundColor: "#F5E0B0",
                      border: "1px solid #E0BC70",
                    }}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Footer info */}
        <div className="p-4 border-t border-line text-[11px] text-muted font-mono space-y-1">
          <div className="flex justify-between">
            <span>Enforcement:</span>
            <span className="text-dark font-semibold">Strict Gateway</span>
          </div>
          <div className="flex justify-between">
            <span>LLM Tool Execution:</span>
            <span className="text-[#2F5A2A] font-semibold">Blocked Direct</span>
          </div>
          <div className="pt-2 text-muted/70 text-[10px] text-center">
            v1.0.0 • Deterministic Kernel
          </div>
        </div>
      </aside>
    </>
  );
}
