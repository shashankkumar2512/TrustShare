// client/src/features/analytics/components/charts/ChartTooltip.js

import React from "react";
import { useTheme } from "../../../../context/ThemeContext";

export default function ChartTooltip({ active, payload, label }) {
  const { theme } = useTheme();

  if (!active || !payload?.length) return null;

  return (
    <div className={`an-tooltip an-tooltip--${theme}`}>
      {label && <p className="an-tooltip-label">{label}</p>}
      {payload.map((entry) => (
        <div key={entry.name} className="an-tooltip-row">
          <span
            className="an-tooltip-dot"
            style={{ background: entry.color ?? entry.fill }}
          />
          <span className="an-tooltip-name">{entry.name}:</span>
          <span className="an-tooltip-value">
            {typeof entry.value === "number"
              ? entry.value.toLocaleString()
              : entry.value}
          </span>
        </div>
      ))}
    </div>
  );
}