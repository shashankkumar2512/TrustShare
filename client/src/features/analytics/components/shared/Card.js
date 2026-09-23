// client/src/features/analytics/components/shared/Card.js

import React from "react";
import { motion } from "framer-motion";

export default function Card({
  children,
  className = "",
  noPadding = false,
  delay     = 0,
  style     = {},
}) {
  return (
    <motion.div
      className={`an-card ${noPadding ? "an-card--no-padding" : ""} ${className}`}
      style={style}
      initial={{ opacity: 0, y: 20, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        duration: 0.55,
        delay,
        ease: [0.32, 0.72, 0, 1],
      }}
      whileHover={{
        y: -4,
        boxShadow:   "var(--an-card-shadow-hover)",
        borderColor: "var(--an-card-border-hover)",
        transition: {
          duration: 0.3,
          ease:     [0.32, 0.72, 0, 1],
        },
      }}
    >
      {children}
    </motion.div>
  );
}

export function CardHeader({ title, right, borderBottom = false }) {
  return (
    <div className={`an-card-header ${borderBottom ? "an-card-header--border" : ""}`}>
      <h3 className="an-card-title">{title}</h3>
      {right && <div className="an-card-header-right">{right}</div>}
    </div>
  );
}