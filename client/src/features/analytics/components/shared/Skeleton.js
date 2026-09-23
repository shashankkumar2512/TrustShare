// client/src/features/analytics/components/shared/Skeleton.js

import React from "react";
import { motion } from "framer-motion";

const EASE        = [0.32, 0.72, 0, 1];   
const PULSE_DUR   = 3.2;                  
const SHIMMER_DUR = 1.8;                  

function SkeletonBreath({ children, delay = 0, style = {}, className = "" }) {
  return (
    <motion.div
      className={className}
      style={style}
      animate={{
        opacity: [1, 0.5, 1],
        scale:   [1, 0.997, 1],
      }}
      transition={{
        duration: PULSE_DUR,
        delay,
        repeat:   Infinity,
        ease:     "easeInOut",
      }}
    >
      {children}
    </motion.div>
  );
}

export default function Skeleton({ className = "", style = {}, delay = 0 }) {
  return (
    <motion.div
      className={`an-skeleton ${className}`}
      style={style}
      aria-hidden="true"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.35, delay, ease: EASE }}
    />
  );
}

export function ChartSkeleton({ height = 200 }) {
  const bars = [55, 72, 48, 85, 63, 90, 77];

  return (
    <SkeletonBreath delay={0.05}>
      <div
        className="an-chart-skeleton"
        style={{ height }}
        aria-hidden="true"
      >
        <div className="an-chart-skeleton-bars">
          {bars.map((h, i) => (
            <motion.div
              key={i}
              className="an-chart-skeleton-bar"
              style={{
                height:         `${h}%`,
                animationDelay: `${i * 0.1}s`,
                transformOrigin: "bottom",
              }}
              initial={{ scaleY: 0, opacity: 0 }}
              animate={{ scaleY: 1, opacity: 1 }}
              transition={{
                duration: 0.5,
                delay:    i * 0.06,
                ease:     EASE,
              }}
            />
          ))}
        </div>

        {/* X-axis label stubs */}
        <div className="an-chart-skeleton-labels">
          {bars.map((_, i) => (
            <Skeleton
              key={i}
              className="an-skeleton-label"
              delay={0.35 + i * 0.04}
            />
          ))}
        </div>
      </div>
    </SkeletonBreath>
  );
}

export function AreaChartSkeleton({ height = 200 }) {
  /* Six x-axis label widths that look natural */
  const xLabelWidths = [38, 32, 36, 28, 34, 30];

  return (
    <SkeletonBreath delay={0.05}>
      <div
        style={{
          width:         "100%",
          height,
          display:       "flex",
          flexDirection: "column",
          gap:           10,
          padding:       "0 8px",
        }}
        aria-hidden="true"
      >
        {/* SVG wave area */}
        <motion.div
          style={{
            flex:         1,
            borderRadius: 10,
            overflow:     "hidden",
            position:     "relative",
          }}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.08, ease: EASE }}
        >
          <svg
            width="100%"
            height="100%"
            viewBox="0 0 400 150"
            preserveAspectRatio="none"
          >
            <defs>
              {/* Gradient fill below the line */}
              <linearGradient id="sk-area-fill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%"
                  stopColor="var(--an-skeleton-via)"
                  stopOpacity="0.9" />
                <stop offset="100%"
                  stopColor="var(--an-skeleton-from)"
                  stopOpacity="0.15" />
              </linearGradient>
            </defs>

            {/* Filled area — fades in */}
            <motion.path
              d="M0,110 C50,90 100,55 160,70
                 C210,85 260,35 310,52
                 C345,65 370,48 400,55
                 L400,150 L0,150 Z"
              fill="url(#sk-area-fill)"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.25, ease: EASE }}
            />

            {/* Stroke line — draws itself in */}
            <motion.path
              d="M0,110 C50,90 100,55 160,70
                 C210,85 260,35 310,52
                 C345,65 370,48 400,55"
              fill="none"
              stroke="var(--an-skeleton-via)"
              strokeWidth="2.5"
              strokeLinecap="round"
              pathLength="1"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 1 }}
              transition={{ duration: 1.1, delay: 0.18, ease: EASE }}
            />

            {/* Data-point dots cascade in after the line */}
            {[
              [0,   110], [80,  70],  [160, 70],
              [240, 45],  [320, 52],  [400, 55],
            ].map(([cx, cy], i) => (
              <motion.circle
                key={i}
                cx={cx} cy={cy} r={4}
                fill="var(--an-skeleton-via)"
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{
                  duration: 0.28,
                  delay:    0.65 + i * 0.07,
                  ease:     EASE,
                }}
              />
            ))}
          </svg>
        </motion.div>

        {/* X-axis labels */}
        <div
          style={{
            display:        "flex",
            justifyContent: "space-between",
            padding:        "0 4px",
          }}
        >
          {xLabelWidths.map((w, i) => (
            <Skeleton
              key={i}
              style={{ width: w, height: 10 }}
              delay={0.55 + i * 0.05}
            />
          ))}
        </div>
      </div>
    </SkeletonBreath>
  );
}

export function LineChartSkeleton({ height = 200 }) {
  return (
    <SkeletonBreath delay={0.05}>
      <div
        style={{ width: "100%", height, padding: "0 8px" }}
        aria-hidden="true"
      >
        <svg
          width="100%"
          height="100%"
          viewBox="0 0 400 160"
          preserveAspectRatio="none"
        >
          {/* Horizontal grid lines */}
          {[35, 75, 115].map((y, i) => (
            <motion.line
              key={i}
              x1="0" y1={y} x2="400" y2={y}
              stroke="var(--an-skeleton-from)"
              strokeWidth="1"
              strokeDasharray="4 6"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3, delay: i * 0.06 }}
            />
          ))}

          {/* Success line (solid) — draws in first */}
          <motion.path
            d="M0,105 C55,85 110,58 165,72
               C215,84 265,38 315,54
               C348,66 372,50 400,57"
            fill="none"
            stroke="var(--an-skeleton-via)"
            strokeWidth="2.5"
            strokeLinecap="round"
            pathLength="1"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{ duration: 1.0, delay: 0.15, ease: EASE }}
          />

          {/* Failed line (dashed, lighter) — draws in slightly after */}
          <motion.path
            d="M0,132 C55,128 110,122 165,130
               C215,137 265,120 315,127
               C348,133 372,122 400,126"
            fill="none"
            stroke="var(--an-skeleton-from)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeDasharray="5 4"
            pathLength="1"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.75 }}
            transition={{ duration: 1.0, delay: 0.30, ease: EASE }}
          />

          {/* Dots on failed line */}
          {[
            [0, 132], [80, 122], [165, 130],
            [245, 122], [320, 127], [400, 126],
          ].map(([cx, cy], i) => (
            <motion.circle
              key={i}
              cx={cx} cy={cy} r={3}
              fill="var(--an-skeleton-from)"
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 0.8 }}
              transition={{
                duration: 0.22,
                delay:    0.7 + i * 0.06,
                ease:     EASE,
              }}
            />
          ))}
        </svg>
      </div>
    </SkeletonBreath>
  );
}

export function BarChartSkeleton({ height = 200 }) {
  /* [upload%, download%] pairs — proportional to realistic data */
  const groups = [
    [68, 44], [82, 58], [52, 36],
    [91, 72], [62, 42], [77, 52], [86, 62],
  ];

  return (
    <SkeletonBreath delay={0.05}>
      <div
        style={{
          width:         "100%",
          height,
          display:       "flex",
          flexDirection: "column",
          gap:           8,
          padding:       "0 8px",
        }}
        aria-hidden="true"
      >
        {/* Bar area */}
        <div
          style={{
            flex:       1,
            display:    "flex",
            alignItems: "flex-end",
            gap:        10,
            padding:    "0 4px",
          }}
        >
          {groups.map(([h1, h2], i) => (
            <div
              key={i}
              style={{
                flex:       1,
                display:    "flex",
                alignItems: "flex-end",
                gap:        3,
                height:     "100%",
              }}
            >
              {/* Upload bar */}
              <motion.div
                className="an-skeleton"
                style={{
                  flex:            1,
                  height:          `${h1}%`,
                  borderRadius:    "5px 5px 0 0",
                  transformOrigin: "bottom",
                }}
                initial={{ scaleY: 0, opacity: 0 }}
                animate={{ scaleY: 1, opacity: 1 }}
                transition={{
                  duration: 0.52,
                  delay:    i * 0.07,
                  ease:     EASE,
                }}
              />
              {/* Download bar — slightly lighter */}
              <motion.div
                className="an-skeleton"
                style={{
                  flex:            1,
                  height:          `${h2}%`,
                  borderRadius:    "5px 5px 0 0",
                  transformOrigin: "bottom",
                  opacity:         0.55,
                }}
                initial={{ scaleY: 0, opacity: 0 }}
                animate={{ scaleY: 1, opacity: 0.55 }}
                transition={{
                  duration: 0.52,
                  delay:    i * 0.07 + 0.05,
                  ease:     EASE,
                }}
              />
            </div>
          ))}
        </div>

        {/* X-axis labels */}
        <div
          style={{
            display:        "flex",
            justifyContent: "space-between",
            padding:        "0 2px",
          }}
        >
          {groups.map((_, i) => (
            <Skeleton
              key={i}
              style={{ width: 28, height: 10 }}
              delay={0.42 + i * 0.05}
            />
          ))}
        </div>
      </div>
    </SkeletonBreath>
  );
}


export function KPICardSkeleton({ index = 0 }) {
  const base = index * 0.07;

  return (
    <SkeletonBreath
      delay={base + 0.04}
      className="an-kpi-card an-kpi-card--skeleton"
      style={{ minHeight: 220 }}
    >
      {/* Icon tile — pops in with a spring scale */}
      <motion.div
        initial={{ opacity: 0, scale: 0.75 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.38, delay: base, ease: EASE }}
      >
        <Skeleton className="an-skeleton--icon" />
      </motion.div>

      {/* Value + label */}
      <div className="an-kpi-body">
        <div className="an-kpi-value-row">
          <Skeleton className="an-skeleton--value" delay={base + 0.09} />
        </div>
        <Skeleton className="an-skeleton--label" delay={base + 0.13} />
      </div>

      {/* Sub text */}
      <Skeleton className="an-skeleton--sub" delay={base + 0.17} />
    </SkeletonBreath>
  );
}

export function KPIGridSkeleton({ count = 4 }) {
  return (
    <div className="an-kpi-grid" aria-hidden="true">
      {Array.from({ length: count }).map((_, i) => (
        <KPICardSkeleton key={i} index={i} />
      ))}
    </div>
  );
}

export function TopFilesSkeleton({ rows = 5 }) {
  /* Widths mirror the real ranked progress-bar proportions */
  const barWidths = [100, 72, 54, 38, 27];

  return (
    <SkeletonBreath delay={0.06}>
      <div className="an-top-files" aria-hidden="true">
        {Array.from({ length: rows }).map((_, i) => (
          <motion.div
            key={i}
            className="an-top-file-skeleton"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.38, delay: i * 0.06, ease: EASE }}
          >
            {/* Rank + name + stats row */}
            <div className="an-top-file-skeleton-row">
              <Skeleton
                style={{ width: 14, height: 12, flexShrink: 0 }}
                delay={i * 0.06 + 0.05}
              />
              <Skeleton
                style={{ width: `${56 - i * 5}%`, height: 12 }}
                delay={i * 0.06 + 0.07}
              />
              <Skeleton
                style={{ width: 54, height: 12 }}
                delay={i * 0.06 + 0.09}
              />
            </div>

            {/* Progress bar — grows from left */}
            <motion.div
              className="an-skeleton"
              style={{
                transformOrigin: "left center",
                width:           `${barWidths[i] ?? 30}%`,
                height:          4,
                borderRadius:    999,
              }}
              initial={{ scaleX: 0, opacity: 0 }}
              animate={{ scaleX: 1, opacity: 1 }}
              transition={{
                duration: 0.65,
                delay:    i * 0.06 + 0.13,
                ease:     EASE,
              }}
            />
          </motion.div>
        ))}
      </div>
    </SkeletonBreath>
  );
}

export function TopUsersSkeleton({ rows = 5 }) {
  /* Name widths vary per row to look natural */
  const nameWidths  = ["58%", "50%", "62%", "46%", "54%"];
  const emailWidths = ["36%", "30%", "40%", "28%", "34%"];

  return (
    <SkeletonBreath delay={0.06}>
      <div className="an-topusers-list" aria-hidden="true">
        {Array.from({ length: rows }).map((_, i) => (
          <motion.div
            key={i}
            className="an-topuser-skeleton"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: i * 0.07, ease: EASE }}
          >
            {/* Rank medal / number */}
            <Skeleton
              className="an-skeleton--dot"
              delay={i * 0.07 + 0.04}
            />

            {/* Avatar rounded square */}
            <Skeleton
              style={{ width: 40, height: 40, borderRadius: 12, flexShrink: 0 }}
              delay={i * 0.07 + 0.06}
            />

            {/* Name + email + progress */}
            <div className="an-topuser-skeleton-body">
              {/* Top row: name + count */}
              <div
                style={{
                  display:        "flex",
                  justifyContent: "space-between",
                  alignItems:     "center",
                  marginBottom:   4,
                }}
              >
                <Skeleton
                  style={{ width: nameWidths[i % nameWidths.length], height: 13 }}
                  delay={i * 0.07 + 0.08}
                />
                <Skeleton
                  style={{ width: 36, height: 13 }}
                  delay={i * 0.07 + 0.09}
                />
              </div>

              {/* Email */}
              <Skeleton
                style={{ width: emailWidths[i % emailWidths.length], height: 10 }}
                delay={i * 0.07 + 0.11}
              />

              {/* Progress bar — grows from left, shorter each row */}
              <motion.div
                className="an-skeleton"
                style={{
                  transformOrigin: "left center",
                  width:           `${88 - i * 13}%`,
                  height:          4,
                  borderRadius:    999,
                  marginTop:       7,
                }}
                initial={{ scaleX: 0, opacity: 0 }}
                animate={{ scaleX: 1, opacity: 1 }}
                transition={{
                  duration: 0.68,
                  delay:    i * 0.07 + 0.15,
                  ease:     EASE,
                }}
              />
            </div>
          </motion.div>
        ))}
      </div>
    </SkeletonBreath>
  );
}

export function RecentActivitySkeleton({ rows = 5 }) {
  const nameWidths = ["44%", "36%", "50%", "40%", "46%"];
  const metaWidths = ["28%", "22%", "32%", "26%", "20%"];

  return (
    <SkeletonBreath delay={0.06}>
      <div className="an-recent-list" aria-hidden="true">
        {Array.from({ length: rows }).map((_, i) => (
          <motion.div
            key={i}
            className="an-recent-skeleton"
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.36, delay: i * 0.06, ease: EASE }}
          >
            {/* Event icon */}
            <Skeleton
              className="an-skeleton--icon-sm"
              delay={i * 0.06 + 0.04}
            />

            {/* Event type + meta */}
            <div style={{ flex: 1 }}>
              <Skeleton
                style={{ width: nameWidths[i % nameWidths.length], height: 12 }}
                delay={i * 0.06 + 0.06}
              />
              <Skeleton
                style={{
                  width:     metaWidths[i % metaWidths.length],
                  height:    10,
                  marginTop: 5,
                }}
                delay={i * 0.06 + 0.09}
              />
            </div>

            {/* Timestamp */}
            <Skeleton
              style={{ width: 44, height: 10, flexShrink: 0 }}
              delay={i * 0.06 + 0.11}
            />
          </motion.div>
        ))}
      </div>
    </SkeletonBreath>
  );
}

export function TimelineSkeleton({ rows = 5 }) {
  const labelWidths  = ["72%", "60%", "78%", "54%", "66%"];
  const detailWidths = ["92%", "84%", "96%", "78%", "88%"];

  return (
    <SkeletonBreath delay={0.06}>
      <div className="an-timeline" aria-hidden="true">
        {Array.from({ length: rows }).map((_, i) => (
          <motion.div
            key={i}
            className="an-timeline-skeleton"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.38, delay: i * 0.07, ease: EASE }}
          >
            {/* Severity ring + dot */}
            <Skeleton
              className="an-skeleton--dot"
              delay={i * 0.07 + 0.04}
            />

            {/* Label + badge + detail + time */}
            <div className="an-timeline-skeleton-body">
              {/* Top: label + badge pill */}
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Skeleton
                  style={{ width: labelWidths[i % labelWidths.length], height: 12 }}
                  delay={i * 0.07 + 0.06}
                />
                <Skeleton
                  style={{ width: 44, height: 18, borderRadius: 999 }}
                  delay={i * 0.07 + 0.08}
                />
              </div>

              {/* Detail sentence */}
              <Skeleton
                style={{
                  width:     detailWidths[i % detailWidths.length],
                  height:    10,
                  marginTop: 7,
                }}
                delay={i * 0.07 + 0.10}
              />

              {/* Timestamp */}
              <Skeleton
                style={{ width: "34%", height: 9, marginTop: 5 }}
                delay={i * 0.07 + 0.12}
              />
            </div>
          </motion.div>
        ))}
      </div>
    </SkeletonBreath>
  );
}

export function UnauthorizedSkeleton({ rows = 4 }) {
  return (
    <SkeletonBreath delay={0.06}>
      <div className="an-unauth-list" aria-hidden="true">
        {Array.from({ length: rows }).map((_, i) => (
          <motion.div
            key={i}
            className="an-unauth-skeleton"
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.38, delay: i * 0.07, ease: EASE }}
          >
            {/* Shield icon */}
            <Skeleton
              className="an-skeleton--icon-sm"
              delay={i * 0.07 + 0.04}
            />

            {/* IP + location */}
            <div style={{ flex: "1.4" }}>
              <Skeleton
                style={{ width: "68%", height: 13 }}
                delay={i * 0.07 + 0.06}
              />
              <Skeleton
                style={{ width: "44%", height: 10, marginTop: 4 }}
                delay={i * 0.07 + 0.08}
              />
            </div>

            {/* Target path */}
            <Skeleton
              style={{ flex: "1.6", height: 12 }}
              delay={i * 0.07 + 0.09}
            />

            {/* Attempt count */}
            <Skeleton
              style={{ width: 58, height: 12 }}
              delay={i * 0.07 + 0.10}
            />

            {/* Timestamp */}
            <Skeleton
              style={{ width: 46, height: 10 }}
              delay={i * 0.07 + 0.11}
            />

            {/* Status pill */}
            <Skeleton
              style={{ width: 70, height: 24, borderRadius: 999 }}
              delay={i * 0.07 + 0.13}
            />
          </motion.div>
        ))}
      </div>
    </SkeletonBreath>
  );
}

export function SystemHealthSkeleton({ sections = 4 }) {
  const tileCounts = [4, 2, 4, 2]; // mirrors SECTIONS

  return (
    <SkeletonBreath delay={0.06}>
      <div className="an-system-sections" aria-hidden="true">
        {Array.from({ length: sections }).map((_, s) => (
          <motion.div
            key={s}
            className="an-system-section"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.38, delay: s * 0.09, ease: EASE }}
          >
            {/* Section label */}
            <Skeleton
              style={{ width: "30%", height: 10, marginBottom: 8 }}
              delay={s * 0.09 + 0.04}
            />

            {/* Stat tile grid */}
            <div className="an-system-grid">
              {Array.from({ length: tileCounts[s] ?? 2 }).map((_, t) => (
                <motion.div
                  key={t}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{
                    duration: 0.33,
                    delay:    s * 0.09 + t * 0.05 + 0.07,
                    ease:     EASE,
                  }}
                >
                  <Skeleton style={{ height: 56, borderRadius: 12 }} />
                </motion.div>
              ))}
            </div>
          </motion.div>
        ))}
      </div>
    </SkeletonBreath>
  );
}

export function SecurityScoreSkeleton() {
  const r    = 70;
  const circ = 2 * Math.PI * r;       // ≈ 440
  const arc  = circ * 0.75;           // 270° track

  return (
    <SkeletonBreath delay={0.08}>
      <div className="an-secscore-skeleton" aria-hidden="true">

        {/* ── Animated gauge arc ── */}
        <motion.div
          style={{ position: "relative", flexShrink: 0 }}
          initial={{ opacity: 0, scale: 0.82 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.55, delay: 0.05, ease: EASE }}
        >
          <svg
            width="180" height="180"
            viewBox="0 0 180 180"
            style={{ transform: "rotate(135deg)" }}
          >
            {/* Static track (270°) */}
            <circle
              cx="90" cy="90" r={r}
              fill="none"
              stroke="var(--an-skeleton-from)"
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={`${arc} ${circ - arc}`}
            />

            {/* Pulsing progress arc */}
            <motion.circle
              cx="90" cy="90" r={r}
              fill="none"
              stroke="var(--an-skeleton-via)"
              strokeWidth="12"
              strokeLinecap="round"
              animate={{
                strokeDasharray: [
                  `0 ${circ}`,
                  `${arc * 0.65} ${circ}`,
                  `0 ${circ}`,
                ],
              }}
              transition={{
                duration: PULSE_DUR,
                repeat:   Infinity,
                ease:     "easeInOut",
              }}
            />
          </svg>

          {/* Center: score value + /100 */}
          <div
            style={{
              position:      "absolute",
              top: "50%", left: "50%",
              transform:     "translate(-50%, -50%)",
              display:       "flex",
              flexDirection: "column",
              alignItems:    "center",
              gap:           6,
            }}
          >
            <Skeleton
              style={{ width: 56, height: 44, borderRadius: 10 }}
              delay={0.22}
            />
            <Skeleton style={{ width: 32, height: 11 }} delay={0.27} />
          </div>
        </motion.div>

        {/* ── Breakdown ── */}
        <div
          style={{
            display:       "flex",
            flexDirection: "column",
            gap:           12,
            flex:          1,
          }}
        >
          {/* Section title */}
          <Skeleton style={{ width: "46%", height: 10 }} delay={0.18} />

          {/* 3 breakdown rows */}
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              style={{ display: "flex", flexDirection: "column", gap: 6 }}
            >
              <div
                style={{
                  display:        "flex",
                  justifyContent: "space-between",
                  alignItems:     "center",
                }}
              >
                <Skeleton
                  style={{ width: `${68 - i * 9}%`, height: 12 }}
                  delay={0.22 + i * 0.07}
                />
                <Skeleton
                  style={{ width: 28, height: 12 }}
                  delay={0.25 + i * 0.07}
                />
              </div>

              {/* Progress bar — extends from left */}
              <motion.div
                className="an-skeleton"
                style={{
                  transformOrigin: "left center",
                  width:           "100%",
                  height:          5,
                  borderRadius:    999,
                }}
                initial={{ scaleX: 0, opacity: 0 }}
                animate={{ scaleX: 1, opacity: 1 }}
                transition={{
                  duration: 0.65,
                  delay:    0.30 + i * 0.09,
                  ease:     EASE,
                }}
              />
            </div>
          ))}

          {/* 3 stat tiles */}
          <div
            style={{
              display:             "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap:                 8,
              paddingTop:          14,
              marginTop:           4,
              borderTop:           "1px solid var(--an-divider)",
            }}
          >
            {[0, 1, 2].map((j) => (
              <motion.div
                key={j}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  duration: 0.33,
                  delay:    0.52 + j * 0.06,
                  ease:     EASE,
                }}
              >
                <Skeleton style={{ height: 52, borderRadius: 10 }} />
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </SkeletonBreath>
  );
}

export function MFAAdoptionSkeleton() {
  const r    = 55;
  const circ = 2 * Math.PI * r; // ≈ 346

  return (
    <SkeletonBreath delay={0.08}>
      <div className="an-mfa-skeleton" aria-hidden="true">

        {/* ── Spinning donut ── */}
        <motion.div
          style={{ position: "relative", flexShrink: 0 }}
          initial={{ opacity: 0, scale: 0.82 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.55, delay: 0.05, ease: EASE }}
        >
          <svg width="140" height="140" viewBox="0 0 140 140">
            {/* Track ring */}
            <circle
              cx="70" cy="70" r={r}
              fill="none"
              stroke="var(--an-skeleton-from)"
              strokeWidth="14"
            />
            {/* Spinning arc */}
            <motion.circle
              cx="70" cy="70" r={r}
              fill="none"
              stroke="var(--an-skeleton-via)"
              strokeWidth="14"
              strokeLinecap="round"
              strokeDasharray={`${circ * 0.62} ${circ * 0.38}`}
              style={{
                transform:       "rotate(-90deg)",
                transformOrigin: "50% 50%",
              }}
              animate={{ rotate: ["-90deg", "270deg"] }}
              transition={{
                duration: PULSE_DUR * 1.15,
                repeat:   Infinity,
                ease:     "linear",
              }}
            />
          </svg>

          {/* Center: % number + "Adopted" */}
          <div
            style={{
              position:      "absolute",
              top: "50%", left: "50%",
              transform:     "translate(-50%, -50%)",
              display:       "flex",
              flexDirection: "column",
              alignItems:    "center",
              gap:           4,
            }}
          >
            <Skeleton style={{ width: 44, height: 30, borderRadius: 8 }} delay={0.22} />
            <Skeleton style={{ width: 36, height: 9  }} delay={0.27} />
          </div>
        </motion.div>

        {/* ── Right panel ── */}
        <div
          style={{
            display:       "flex",
            flexDirection: "column",
            gap:           10,
            flex:          1,
          }}
        >
          {/* 2-column stat tiles */}
          <div
            style={{
              display:             "grid",
              gridTemplateColumns: "1fr 1fr",
              gap:                 8,
            }}
          >
            {[0, 1].map((i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{
                  duration: 0.40,
                  delay:    0.18 + i * 0.09,
                  ease:     EASE,
                }}
              >
                <Skeleton style={{ height: 64, borderRadius: 12 }} />
              </motion.div>
            ))}
          </div>

          {/* Total users row */}
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.36, delay: 0.36, ease: EASE }}
          >
            <Skeleton style={{ width: "100%", height: 36, borderRadius: 10 }} />
          </motion.div>

          {/* Recommendation banner */}
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.36, delay: 0.46, ease: EASE }}
          >
            <Skeleton style={{ width: "100%", height: 36, borderRadius: 12 }} />
          </motion.div>
        </div>
      </div>
    </SkeletonBreath>
  );
}

export function HeatmapSkeleton({ rows = 7, cols = 24 }) {
  return (
    <SkeletonBreath delay={0.08}>
      <div className="an-heatmap-skeleton" aria-hidden="true">
        {Array.from({ length: rows }).map((_, r) => (
          <div key={r} className="an-heatmap-skeleton-row">
            {Array.from({ length: cols }).map((_, c) => {
              const diag = (r + c) * 0.011; // diagonal wave delay
              return (
                <motion.div
                  key={c}
                  className="an-skeleton"
                  style={{
                    height:           18,
                    borderRadius:     4,
                    animationDelay:   `${diag}s`,
                  }}
                  initial={{ opacity: 0, scale: 0.65 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{
                    duration: 0.22,
                    delay:    diag,
                    ease:     EASE,
                  }}
                />
              );
            })}
          </div>
        ))}

        {/* Footer: legend scale + hover-info placeholder */}
        <div
          style={{
            display:        "flex",
            justifyContent: "space-between",
            alignItems:     "center",
            marginTop:      16,
            paddingTop:     14,
            borderTop:      "1px solid var(--an-divider)",
          }}
        >
          {/* Legend scale */}
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Skeleton style={{ width: 24, height: 10 }} delay={0.42} />
            <div style={{ display: "flex", gap: 3 }}>
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton
                  key={i}
                  style={{ width: 16, height: 14, borderRadius: 3 }}
                  delay={0.44 + i * 0.03}
                />
              ))}
            </div>
            <Skeleton style={{ width: 28, height: 10 }} delay={0.64} />
          </div>

          {/* Hover-info pill */}
          <Skeleton
            style={{ width: 140, height: 28, borderRadius: 8 }}
            delay={0.52}
          />
        </div>
      </div>
    </SkeletonBreath>
  );
}

export function DonutSkeleton({
  legendRows  = 5,
  size        = 120,
  showCenter  = false,
}) {
  const r    = size / 2 - 12;
  const circ = 2 * Math.PI * r;

  return (
    <SkeletonBreath delay={0.08}>
      <div className="an-donut-skeleton" aria-hidden="true">

        {/* ── Spinning donut arc ── */}
        <motion.div
          style={{ flexShrink: 0, position: "relative" }}
          initial={{ opacity: 0, scale: 0.82 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.52, delay: 0.05, ease: EASE }}
        >
          <svg
            width={size} height={size}
            viewBox={`0 0 ${size} ${size}`}
          >
            {/* Track */}
            <circle
              cx={size / 2} cy={size / 2} r={r}
              fill="none"
              stroke="var(--an-skeleton-from)"
              strokeWidth="10"
            />

            {/* Rotating arc */}
            <motion.circle
              cx={size / 2} cy={size / 2} r={r}
              fill="none"
              stroke="var(--an-skeleton-via)"
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={`${circ * 0.58} ${circ * 0.42}`}
              style={{
                transform:       "rotate(-90deg)",
                transformOrigin: "50% 50%",
              }}
              animate={{ rotate: ["-90deg", "270deg"] }}
              transition={{
                duration: PULSE_DUR * 1.1,
                repeat:   Infinity,
                ease:     "linear",
              }}
            />
          </svg>

          {/* Center total label (FileTypeDonut only) */}
          {showCenter && (
            <div
              style={{
                position:      "absolute",
                top: "50%", left: "50%",
                transform:     "translate(-50%, -50%)",
                display:       "flex",
                flexDirection: "column",
                alignItems:    "center",
                gap:           3,
              }}
            >
              <Skeleton
                style={{ width: 36, height: 26, borderRadius: 6 }}
                delay={0.22}
              />
              <Skeleton style={{ width: 28, height: 9 }} delay={0.27} />
            </div>
          )}
        </motion.div>

        {/* ── Legend rows ── */}
        <div className="an-donut-legend-skeleton">
          {Array.from({ length: legendRows }).map((_, i) => (
            <motion.div
              key={i}
              style={{ display: "flex", alignItems: "center", gap: 10 }}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{
                duration: 0.36,
                delay:    0.14 + i * 0.07,
                ease:     EASE,
              }}
            >
              {/* Color dot */}
              <Skeleton
                style={{
                  width:        10,
                  height:       10,
                  borderRadius: "50%",
                  flexShrink:   0,
                }}
                delay={0.17 + i * 0.07}
              />
              {/* Name label — decreasing width looks natural */}
              <Skeleton
                className="an-skeleton--legend-row"
                style={{ flex: 1, width: `${70 - i * 9}%` }}
                delay={0.19 + i * 0.07}
              />
              {/* Value */}
              <Skeleton
                style={{ width: 30, height: 12 }}
                delay={0.21 + i * 0.07}
              />
            </motion.div>
          ))}
        </div>
      </div>
    </SkeletonBreath>
  );
}

export function HeaderSkeleton() {
  return (
    <SkeletonBreath delay={0}>
      <div className="an-header" aria-hidden="true">

        {/* ── Left: title + subtitle + live indicator ── */}
        <div className="an-header-left">
          {/* "Analytics" title */}
          <Skeleton
            style={{ width: 138, height: 36, borderRadius: 10 }}
            delay={0}
          />
          {/* Subtitle */}
          <Skeleton
            style={{ width: 300, height: 14, borderRadius: 6, marginTop: 8 }}
            delay={0.05}
          />
          {/* Live indicator pill */}
          <Skeleton
            style={{
              width:        225,
              height:       26,
              borderRadius: 999,
              marginTop:    10,
            }}
            delay={0.08}
          />
        </div>

        {/* ── Right: tab switcher + date dropdown + buttons ── */}
        <div className="an-header-right">

          {/* Tab switcher pill — "File Analytics | Security" */}
          <motion.div
            style={{
              display:      "flex",
              padding:      4,
              background:   "var(--an-tab-bg)",
              border:       "1px solid var(--an-tab-border)",
              borderRadius: 14,
              gap:          2,
            }}
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1, ease: [0.32, 0.72, 0, 1] }}
          >
            {/* Tab 1 — active */}
            <Skeleton
              style={{
                width:        120,
                height:       36,
                borderRadius: 10,
              }}
              delay={0.12}
            />
            {/* Tab 2 — inactive */}
            <Skeleton
              style={{
                width:        90,
                height:       36,
                borderRadius: 10,
                opacity:      0.5,
              }}
              delay={0.15}
            />
          </motion.div>

          {/* Date range dropdown */}
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.18, ease: [0.32, 0.72, 0, 1] }}
          >
            <Skeleton
              style={{
                width:        140,
                height:       40,
                borderRadius: 14,
              }}
              delay={0.18}
            />
          </motion.div>

          {/* Auto-refresh toggle button */}
          <Skeleton
            style={{
              width:        40,
              height:       40,
              borderRadius: 12,
            }}
            delay={0.22}
          />

          {/* Refresh button */}
          <Skeleton
            style={{
              width:        40,
              height:       40,
              borderRadius: 12,
            }}
            delay={0.25}
          />

          {/* Export button */}
          <Skeleton
            style={{
              width:        170,
              height:       40,
              borderRadius: 12,
            }}
            delay={0.28}
          />
        </div>
      </div>
    </SkeletonBreath>
  );
}