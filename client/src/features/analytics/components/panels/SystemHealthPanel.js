// client/src/features/analytics/components/panels/SystemHealthPanel.js

import React from "react";
import { motion } from "framer-motion";
import {
  Activity, Database, Users, FileText, Link2, Zap,
  UserCheck, HardDrive, TrendingUp, Cpu, Clock, CheckCircle2,
} from "lucide-react";
import Card, { CardHeader } from "../shared/Card";
import { SystemHealthSkeleton } from "../shared/Skeleton";

const STAT_ICONS = {
  total_events: Activity,
  events_1h: Clock,
  events_24h: Zap,
  events_7d: TrendingUp,
  total_users: Users,
  active_users_24h: UserCheck,
  total_files: FileText,
  total_storage_mb: HardDrive,
  total_shares: Link2,
  active_shares: Link2,
  db_response_ms: Database,
  success_rate: CheckCircle2,
  python_version: Cpu,
  platform: Cpu,
};

const STAT_UNITS = {
  db_response_ms: "ms",
  total_storage_mb: "MB",
  success_rate: "%",
};

const STAT_COLORS = {
  total_events: { c: "var(--an-kpi-blue)", b: "var(--an-kpi-blue-bg)" },
  events_1h: { c: "var(--an-kpi-indigo)", b: "var(--an-kpi-indigo-bg)" },
  events_24h: { c: "var(--an-kpi-sky)", b: "var(--an-kpi-sky-bg)" },
  events_7d: { c: "var(--an-kpi-emerald)", b: "var(--an-kpi-emerald-bg)" },
  total_users: { c: "var(--an-kpi-blue)", b: "var(--an-kpi-blue-bg)" },
  active_users_24h: { c: "var(--an-kpi-emerald)", b: "var(--an-kpi-emerald-bg)" },
  total_files: { c: "var(--an-kpi-indigo)", b: "var(--an-kpi-indigo-bg)" },
  total_storage_mb: { c: "var(--an-kpi-amber)", b: "var(--an-kpi-amber-bg)" },
  total_shares: { c: "var(--an-kpi-sky)", b: "var(--an-kpi-sky-bg)" },
  active_shares: { c: "var(--an-kpi-emerald)", b: "var(--an-kpi-emerald-bg)" },
  db_response_ms: { c: "var(--an-kpi-blue)", b: "var(--an-kpi-blue-bg)" },
  success_rate: { c: "var(--an-kpi-emerald)", b: "var(--an-kpi-emerald-bg)" },
};

const SECTIONS = [
  {
    key: "activity",
    stats: ["total_events", "events_1h", "events_24h", "events_7d"],
  },
  {
    key: "users",
    stats: ["total_users", "active_users_24h"],
  },
  {
    key: "storage",
    stats: ["total_files", "total_storage_mb", "total_shares", "active_shares"],
  },
  {
    key: "performance",
    stats: ["db_response_ms", "success_rate"],
  },
];

function formatValue(key, value) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") return value.toLocaleString();
  return String(value);
}

export default function SystemHealthPanel({
  stats = {},
  loading = false,
  config = {},
}) {
  const title = config.title || "System Health";
  const labels = config.labels || {};
  const sections = config.sections || {};

  const statusColor =
    stats.status === "healthy" ? "var(--an-kpi-emerald)"
      : stats.status === "slow" ? "var(--an-kpi-amber)"
        : "var(--an-kpi-red)";

  const statusBg =
    stats.status === "healthy" ? "var(--an-kpi-emerald-bg)"
      : stats.status === "slow" ? "var(--an-kpi-amber-bg)"
        : "var(--an-kpi-red-bg)";

  return (
    <Card delay={0.35}>
      <CardHeader
        title={title}
        right={
          !loading && stats.status && (
            <span
              className="an-system-status"
              style={{ color: statusColor }}
            >
              <span
                className="an-system-status-dot"
                style={{
                  background: statusColor,
                  boxShadow: `0 0 0 3px ${statusBg}`,
                }}
              />
              {stats.status}
            </span>
          )
        }
      />

      {loading ? (
        <SystemHealthSkeleton sections={4} />
      ) : (
        <div className="an-system-sections">
          {SECTIONS.map((section, sIdx) => {
            const availableStats = section.stats.filter(
              (k) => stats[k] !== undefined && stats[k] !== null
            );
            if (availableStats.length === 0) return null;

            return (
              <div key={section.key} className="an-system-section">
                <div className="an-system-section-label">
                  {sections[section.key] || section.key}
                </div>
                <div className="an-system-grid">
                  {availableStats.map((k, i) => {
                    const Icon = STAT_ICONS[k] || Activity;
                    const unit = STAT_UNITS[k] || "";
                    const label = labels[k] || k;
                    const color = STAT_COLORS[k]?.c || "var(--an-kpi-blue)";
                    const bg = STAT_COLORS[k]?.b || "var(--an-kpi-blue-bg)";
                    const value = formatValue(k, stats[k]);

                    return (
                      <motion.div
                        key={k}
                        className="an-system-stat"
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{
                          duration: 0.3,
                          delay: sIdx * 0.08 + i * 0.04,
                          ease: [0.32, 0.72, 0, 1],
                        }}
                      >
                        <div
                          className="an-system-stat-icon"
                          style={{ background: bg, color }}
                        >
                          <Icon size={14} />
                        </div>
                        <div className="an-system-stat-body">
                          <div
                            className="an-system-stat-value"
                            style={{
                              color: k === "db_response_ms"
                                ? stats[k] < 100 ? "var(--an-kpi-emerald)"
                                  : stats[k] < 500 ? "var(--an-kpi-amber)"
                                    : "var(--an-kpi-red)"
                                : "var(--an-text-primary)",
                            }}
                          >
                            {value}
                            {unit && <span className="an-system-stat-unit"> {unit}</span>}
                          </div>
                          <div className="an-system-stat-label">{label}</div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            );
          })}

          {/* Runtime footer */}
          {(stats.python_version || stats.platform) && (
            <div className="an-system-footer">
              {stats.platform && (
                <span className="an-system-footer-item">
                  <Cpu size={11} /> {stats.platform}
                </span>
              )}
              {stats.python_version && (
                <span className="an-system-footer-item">
                  Python {stats.python_version}
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </Card>
  );
}