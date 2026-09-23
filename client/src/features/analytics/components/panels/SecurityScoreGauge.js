// client/src/features/analytics/components/panels/SecurityScoreGauge.js

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Shield, TrendingUp, TrendingDown, Minus } from "lucide-react";
import Card from "../shared/Card";
import { SecurityScoreSkeleton } from "../shared/Skeleton";

export default function SecurityScoreGauge({
  scoreData = null,
  loading = false,
  config = {},
}) {
  const title = config.title || "Security Score";
  const subtitle = config.subtitle || "Overall security health";
  const breakdownTitle = config.breakdown_title || "Score Breakdown";
  const loginLabel = config.login_success_label || "Login Success Rate";
  const attackLabel = config.attack_response_label || "Attack Response";
  const failedLabel = config.failed_score_label || "Failed Login Score";
  const emptyMessage = config.empty || "Not enough data to calculate score.";

  const [displayScore, setDisplayScore] = useState(0);

  // Animate score counter
  useEffect(() => {
    if (!scoreData?.score) return;
    const target = scoreData.score;
    const duration = 1200;
    const startTime = Date.now();

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Easing: ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayScore(target * eased);
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [scoreData?.score]);

  if (loading) {
    return (
      <Card delay={0.2}>
        <div className="an-card-header">
          <div>
            <h3 className="an-card-title">{title}</h3>
            <p className="an-chart-meta" style={{ marginTop: 4 }}>
              {subtitle}
            </p>
          </div>
        </div>
        <SecurityScoreSkeleton />
      </Card>
    );
  }

  if (!scoreData || scoreData.score === undefined) {
    return (
      <Card delay={0.2}>
        <div className="an-card-header">
          <div>
            <h3 className="an-card-title">{title}</h3>
            <p className="an-chart-meta" style={{ marginTop: 4 }}>
              {subtitle}
            </p>
          </div>
        </div>
        <div className="an-secscore-empty">
          <Shield size={40} strokeWidth={1.5} />
          <p>{emptyMessage}</p>
        </div>
      </Card>
    );
  }

  const score = scoreData.score;
  const status = scoreData.status;
  const scoreColor = scoreData.color;
  const breakdown = scoreData.breakdown || {};

  // Gauge math (270° arc from -135° to +135°)
  const radius = 70;
  const strokeWidth = 12;
  const circumference = 2 * Math.PI * radius;
  const arcLength = circumference * 0.75; // 270° arc
  const scoreProgress = (displayScore / 100) * arcLength;
  const gapLength = circumference - arcLength;

  // Trend icon
  const getTrendIcon = () => {
    if (score >= 90) return <TrendingUp size={12} strokeWidth={2.5} />;
    if (score < 60) return <TrendingDown size={12} strokeWidth={2.5} />;
    return <Minus size={12} strokeWidth={2.5} />;
  };

  return (
    <Card delay={0.2}>
      <div className="an-card-header">
        <div>
          <h3 className="an-card-title">{title}</h3>
          <p className="an-chart-meta" style={{ marginTop: 4 }}>
            {subtitle}
          </p>
        </div>
        <motion.div
          className="an-secscore-status-badge"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5, duration: 0.3, ease: [0.32, 0.72, 0, 1] }}
          style={{
            background: `${scoreColor}15`,
            color: scoreColor,
            borderColor: `${scoreColor}30`,
          }}
        >
          {getTrendIcon()}
          {status}
        </motion.div>
      </div>

      <div className="an-secscore-container">
        {/* Circular Gauge */}
        <div className="an-secscore-gauge">
          <svg
            width="180"
            height="180"
            viewBox="0 0 180 180"
            style={{ transform: "rotate(135deg)" }}
          >
            {/* Background track */}
            <circle
              cx="90"
              cy="90"
              r={radius}
              fill="none"
              stroke="var(--an-top-file-track-bg)"
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              strokeDasharray={`${arcLength} ${gapLength}`}
            />
            {/* Progress arc */}
            <motion.circle
              cx="90"
              cy="90"
              r={radius}
              fill="none"
              stroke={scoreColor}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              strokeDasharray={`${scoreProgress} ${circumference}`}
              initial={{ strokeDasharray: `0 ${circumference}` }}
              animate={{ strokeDasharray: `${scoreProgress} ${circumference}` }}
              transition={{ duration: 1.2, ease: [0.32, 0.72, 0, 1] }}
              style={{
                filter: `drop-shadow(0 0 8px ${scoreColor}40)`,
              }}
            />
          </svg>

          {/* Center content */}
          <div className="an-secscore-center">
            <motion.div
              className="an-secscore-value"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.4 }}
              style={{ color: scoreColor }}
            >
              {Math.round(displayScore)}
            </motion.div>
            <motion.div
              className="an-secscore-max"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5, duration: 0.3 }}
            >
              / 100
            </motion.div>
          </div>
        </div>

        {/* Breakdown */}
        <div className="an-secscore-breakdown">
          <div className="an-secscore-breakdown-title">{breakdownTitle}</div>

          <BreakdownRow
            label={loginLabel}
            value={breakdown.login_success || 0}
            delay={0.5}
          />
          <BreakdownRow
            label={attackLabel}
            value={breakdown.attack_response || 0}
            delay={0.6}
          />
          <BreakdownRow
            label={failedLabel}
            value={breakdown.failed_score || 0}
            delay={0.7}
          />

          <div className="an-secscore-stats">
            <div className="an-secscore-stat">
              <span className="an-secscore-stat-value">
                {(scoreData.total_logins || 0).toLocaleString()}
              </span>
              <span className="an-secscore-stat-label">Total Logins</span>
            </div>
            <div className="an-secscore-stat">
              <span
                className="an-secscore-stat-value"
                style={{ color: "var(--an-kpi-red)" }}
              >
                {(scoreData.failed || 0).toLocaleString()}
              </span>
              <span className="an-secscore-stat-label">Failed</span>
            </div>
            <div className="an-secscore-stat">
              <span
                className="an-secscore-stat-value"
                style={{ color: "var(--an-kpi-amber)" }}
              >
                {(scoreData.blocked_attacks || 0).toLocaleString()}
              </span>
              <span className="an-secscore-stat-label">Blocked</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}

function BreakdownRow({ label, value, delay }) {
  // Color based on score
  const getColor = (v) => {
    if (v >= 90) return "var(--an-kpi-emerald)";
    if (v >= 75) return "var(--an-kpi-blue)";
    if (v >= 60) return "var(--an-kpi-amber)";
    return "var(--an-kpi-red)";
  };

  const color = getColor(value);

  return (
    <motion.div
      className="an-secscore-row"
      initial={{ opacity: 0, x: 10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay, duration: 0.4, ease: [0.32, 0.72, 0, 1] }}
    >
      <div className="an-secscore-row-top">
        <span className="an-secscore-row-label">{label}</span>
        <span
          className="an-secscore-row-value"
          style={{ color }}
        >
          {Math.round(value)}
        </span>
      </div>
      <div className="an-secscore-row-track">
        <motion.div
          className="an-secscore-row-fill"
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{
            delay: delay + 0.1,
            duration: 0.8,
            ease: [0.32, 0.72, 0, 1],
          }}
          style={{ background: color }}
        />
      </div>
    </motion.div>
  );
}