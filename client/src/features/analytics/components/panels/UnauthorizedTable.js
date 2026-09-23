// client/src/features/analytics/components/panels/UnauthorizedTable.js

import React from "react";
import { motion } from "framer-motion";
import { ShieldOff, MapPin } from "lucide-react";
import Card, { CardHeader } from "../shared/Card";
import { UnauthorizedSkeleton } from "../shared/Skeleton";
import EmptyState from "../shared/EmptyState";

export default function UnauthorizedTable({
  attempts = [],
  loading = false,
  config = {},
}) {
  const title = config.title || "Unauthorized Access Attempts";
  const blockedLabel = config.blocked_label || "blocked";
  const blockedStatus = config.blocked_status || "Blocked";
  const flaggedStatus = config.flagged_status || "Flagged";
  const attemptsLabel = config.attempts_label || "attempts";
  const empty = config.empty || "No unauthorized attempts recorded.";

  const blockedCount = attempts.filter((r) => r.blocked).length;

  return (
    <Card delay={0.25} noPadding>
      <CardHeader
        title={title}
        borderBottom
        right={
          blockedCount > 0 && (
            <span className="an-blocked-badge">
              {blockedCount} {blockedLabel}
            </span>
          )
        }
      />

      {loading ? (
        <UnauthorizedSkeleton rows={4} />
      ) : !attempts.length ? (
        <div className="an-unauth-empty">
          <EmptyState message={empty} />
        </div>
      ) : (
        <div className="an-unauth-list">
          {attempts.map((row, i) => (
            <motion.div
              key={row.id}
              className={`an-unauth-row ${row.blocked ? "an-unauth-row--blocked" : "an-unauth-row--flagged"}`}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{
                duration: 0.35,
                delay: 0.1 + i * 0.06,
                ease: [0.32, 0.72, 0, 1],
              }}
              whileHover={{ x: 2, backgroundColor: "var(--an-unauth-hover-bg)" }}
            >
              {/* Icon */}
              <div className={`an-unauth-icon ${row.blocked ? "an-unauth-icon--blocked" : "an-unauth-icon--flagged"}`}>
                <ShieldOff size={14} />
              </div>

              {/* IP + location */}
              <div className="an-unauth-ip">
                <p className="an-unauth-ip-value">{row.ip}</p>
                <p className="an-unauth-location">
                  <MapPin size={9} /> {row.location}
                </p>
              </div>

              {/* Target */}
              <p className="an-unauth-target">
                → <span>{row.target}</span>
              </p>

              {/* Attempts */}
              <p className="an-unauth-attempts">
                <strong>{row.attempts}</strong> {attemptsLabel}
              </p>

              {/* Time */}
              <p className="an-unauth-time">{row.time}</p>

              {/* Status badge */}
              <span className={`an-unauth-status ${row.blocked ? "an-unauth-status--blocked" : "an-unauth-status--flagged"}`}>
                {row.blocked ? blockedStatus : flaggedStatus}
              </span>
            </motion.div>
          ))}
        </div>
      )}
    </Card>
  );
}