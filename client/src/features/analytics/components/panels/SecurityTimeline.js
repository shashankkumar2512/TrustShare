// client/src/features/analytics/components/panels/SecurityTimeline.js

import React from "react";
import { motion } from "framer-motion";
import Card, { CardHeader } from "../shared/Card";
import { TimelineSkeleton } from "../shared/Skeleton";
import EmptyState from "../shared/EmptyState";

export default function SecurityTimeline({
  events = [],
  loading = false,
  config = {},
  severity = {},
}) {
  const title = config.title || "Security Event Timeline";
  const empty = config.empty || "No security events.";

  const getSeverityMeta = (sev) => severity[sev] || severity.info || { label: sev?.toUpperCase() || "INFO" };

  return (
    <Card delay={0.2} noPadding>
      <CardHeader title={title} borderBottom />

      {loading ? (
        <TimelineSkeleton rows={5} />
      ) : !events.length ? (
        <div className="an-timeline-empty">
          <EmptyState message={empty} />
        </div>
      ) : (
        <div className="an-timeline">
          {events.map((ev, i) => {
            const meta = getSeverityMeta(ev.sev);
            const isLast = i === events.length - 1;

            return (
              <motion.div
                key={ev.id}
                className="an-timeline-item"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  duration: 0.35,
                  delay: 0.1 + i * 0.07,
                  ease: [0.32, 0.72, 0, 1],
                }}
              >
                {/* Connector line */}
                {!isLast && <div className="an-timeline-connector" />}

                {/* Severity ring + dot */}
                <div className={`an-timeline-ring an-timeline-ring--${ev.sev}`}>
                  <div className={`an-timeline-dot an-timeline-dot--${ev.sev}`} />
                </div>

                {/* Content */}
                <div className="an-timeline-body">
                  <div className="an-timeline-top">
                    <span className="an-timeline-label">{ev.label}</span>
                    <span className={`an-timeline-badge an-timeline-badge--${ev.sev}`}>
                      {meta.label}
                    </span>
                  </div>
                  <p className="an-timeline-detail">{ev.detail}</p>
                  <p className="an-timeline-time">{ev.time}</p>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </Card>
  );
}