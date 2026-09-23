// client/src/features/analytics/components/charts/FailedLoginHeatmap.js
/**
 * Failed Login Heatmap — 7 days × 24 hours grid.
 * Shows attack patterns by time of day.
 * All labels + data from DB.
 */

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Flame } from "lucide-react";
import Card from "../shared/Card";
import { HeatmapSkeleton } from "../shared/Skeleton";
import EmptyState from "../shared/EmptyState";

export default function FailedLoginHeatmap({
  heatmapData = null,
  loading = false,
  config = {},
}) {
  const title = config.title || "Failed Login Heatmap";
  const subtitle = config.subtitle || "Attack patterns by day and hour";
  const meta = config.meta || "last 7 days";
  const emptyMsg = config.empty || "No failed login attempts recorded.";
  const lowLabel = config.low_label || "Low";
  const highLabel = config.high_label || "High";

  const [hoveredCell, setHoveredCell] = useState(null);

  if (loading) {
    return (
      <Card delay={0.25}>
        <div className="an-card-header">
          <div>
            <h3 className="an-card-title">{title}</h3>
            <p className="an-chart-meta" style={{ marginTop: 4 }}>
              {subtitle}
            </p>
          </div>
        </div>
        <HeatmapSkeleton rows={7} cols={24} />
      </Card>
    );
  }

  if (!heatmapData || !heatmapData.grid || heatmapData.total === 0) {
    return (
      <Card delay={0.25}>
        <div className="an-card-header">
          <div>
            <h3 className="an-card-title">{title}</h3>
            <p className="an-chart-meta" style={{ marginTop: 4 }}>
              {subtitle}
            </p>
          </div>
        </div>
        <EmptyState message={emptyMsg} />
      </Card>
    );
  }

  const { grid, max_count, total } = heatmapData;
  const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  // Organize grid by day
  const byDay = dayNames.map((day) =>
    grid.filter((cell) => cell.day === day).sort((a, b) => a.hour - b.hour)
  );

  // Get intensity color (0-100%)
  const getIntensity = (count) => {
    if (count === 0) return 0;
    if (max_count === 0) return 0;
    return Math.min(100, (count / max_count) * 100);
  };

  // Get cell color
  const getCellColor = (count) => {
    const intensity = getIntensity(count);
    if (intensity === 0) return "var(--an-top-file-track-bg)";
    // Red intensity from 20% to 100%
    const alpha = 0.15 + (intensity / 100) * 0.75;
    return `rgba(239, 68, 68, ${alpha})`;
  };

  return (
    <Card delay={0.25}>
      <div className="an-card-header">
        <div>
          <h3 className="an-card-title">{title}</h3>
          <p className="an-chart-meta" style={{ marginTop: 4 }}>
            {subtitle}
          </p>
        </div>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4, duration: 0.3, ease: [0.32, 0.72, 0, 1] }}
          className="an-heatmap-badge"
        >
          <Flame size={12} strokeWidth={2.5} />
          {total} attempts · {meta}
        </motion.div>
      </div>

      <div className="an-heatmap-container">
        {/* Hour labels (top) */}
        <div className="an-heatmap-hours">
          <div className="an-heatmap-day-spacer" />
          {Array.from({ length: 24 }).map((_, hour) => (
            <div key={hour} className="an-heatmap-hour-label">
              {hour % 6 === 0 ? `${hour}h` : ""}
            </div>
          ))}
        </div>

        {/* Grid rows */}
        {byDay.map((dayRow, dayIdx) => (
          <motion.div
            key={dayNames[dayIdx]}
            className="an-heatmap-row"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{
              delay: 0.2 + dayIdx * 0.05,
              duration: 0.4,
              ease: [0.32, 0.72, 0, 1],
            }}
          >
            <div className="an-heatmap-day-label">{dayNames[dayIdx]}</div>
            {dayRow.map((cell, hourIdx) => (
              <motion.div
                key={`${dayIdx}-${hourIdx}`}
                className="an-heatmap-cell"
                style={{
                  background: getCellColor(cell.count),
                }}
                onMouseEnter={() => setHoveredCell(cell)}
                onMouseLeave={() => setHoveredCell(null)}
                whileHover={{
                  scale: 1.4,
                  zIndex: 5,
                  transition: { duration: 0.15, ease: [0.32, 0.72, 0, 1] },
                }}
                title={`${cell.day} ${cell.hour}:00 — ${cell.count} attempts`}
              />
            ))}
          </motion.div>
        ))}

        {/* Legend + Hover Info */}
        <div className="an-heatmap-footer">
          <div className="an-heatmap-legend">
            <span className="an-heatmap-legend-label">{lowLabel}</span>
            <div className="an-heatmap-legend-scale">
              {[0.15, 0.3, 0.45, 0.6, 0.75, 0.9].map((alpha, i) => (
                <div
                  key={i}
                  className="an-heatmap-legend-cell"
                  style={{ background: `rgba(239, 68, 68, ${alpha})` }}
                />
              ))}
            </div>
            <span className="an-heatmap-legend-label">{highLabel}</span>
          </div>

          {hoveredCell && hoveredCell.count > 0 && (
            <motion.div
              className="an-heatmap-hover-info"
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.15 }}
            >
              <span className="an-heatmap-hover-time">
                {hoveredCell.day} · {String(hoveredCell.hour).padStart(2, "0")}:00
              </span>
              <span className="an-heatmap-hover-count">
                {hoveredCell.count} {hoveredCell.count === 1 ? "attempt" : "attempts"}
              </span>
            </motion.div>
          )}
        </div>
      </div>
    </Card>
  );
}