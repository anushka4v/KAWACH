import React from "react";

/**
 * StatusBadge component.
 * Purely visual status renderer with soft, light decision pills that stay
 * readable on both beige and middle-brown surfaces.
 * Never makes access control decisions.
 */
export default function StatusBadge({ status, className = "" }) {
  const norm = (status || "").toString().toUpperCase().trim();

  let label = "UNKNOWN";
  let style = {
    color: "#6E5645",
    backgroundColor: "#E5D9C6",
    borderColor: "#C9B396",
  };

  if (norm === "ALLOW" || norm === "ALLOWED") {
    label = "ALLOW";
    style = {
      color: "#2F5A2A",
      backgroundColor: "#CFE3C4",
      borderColor: "#9CC48F",
    };
  } else if (norm === "DENY" || norm === "DENIED") {
    label = "DENY";
    style = {
      color: "#8A2B2B",
      backgroundColor: "#F2CFCB",
      borderColor: "#DB9A94",
    };
  } else if (
    norm === "REQUIRE APPROVAL" ||
    norm === "REQUIRE_APPROVAL" ||
    norm === "PENDING_APPROVAL" ||
    norm === "PENDING"
  ) {
    label = norm === "PENDING" ? "PENDING" : "REQUIRE APPROVAL";
    style = {
      color: "#8A5A12",
      backgroundColor: "#F5E0B0",
      borderColor: "#E0BC70",
    };
  } else if (norm === "APPROVED") {
    label = "APPROVED";
    style = {
      color: "#2F5A2A",
      backgroundColor: "#CFE3C4",
      borderColor: "#9CC48F",
    };
  } else if (norm === "REJECTED") {
    label = "REJECTED";
    style = {
      color: "#8A2B2B",
      backgroundColor: "#F2CFCB",
      borderColor: "#DB9A94",
    };
  } else if (norm === "EXECUTED") {
    label = "EXECUTED";
    style = {
      color: "#2F5A2A",
      backgroundColor: "#DCE7D2",
      borderColor: "#A9C69C",
    };
  } else if (norm === "NOT_EXECUTED") {
    label = "NOT EXECUTED";
    style = {
      color: "#6E5645",
      backgroundColor: "#E5D9C6",
      borderColor: "#C9B396",
    };
  }

  return (
    <span
      style={style}
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider border ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5 opacity-80" />
      {label}
    </span>
  );
}
