import React from "react";

/**
 * Metric summary card for the gateway dashboard.
 * Every metric uses the same middle-brown gallery card so the page reads as
 * one warm, editorial surface; the icon carries the tan accent.
 */
export default function StatCard({
  title,
  value,
  subtext,
  icon,
}) {
  return (
    <div className="k-card k-card-hover p-5">
      <div className="flex items-center justify-between mb-2 gap-3">
        <span className="text-[11px] uppercase tracking-[0.12em] text-on-card-muted font-semibold">
          {title}
        </span>
        {icon && <div className="text-accent-tan text-base leading-none">{icon}</div>}
      </div>
      <div className="text-3xl font-semibold text-on-card tracking-[-0.02em]">
        {value}
      </div>
      {subtext && (
        <div className="mt-2 text-[11px] text-on-card-muted font-mono">{subtext}</div>
      )}
    </div>
  );
}
