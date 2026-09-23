// client/src/features/analytics/components/kpi/KPICard.js

import React from "react";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import useCountUp from "../../hooks/useCountUp";
import { getIcon } from "../../config/iconRegistry";

export default function KPICard({
  iconName,
  colorVar,
  bgVar,
  label,
  value = 0,
  suffix = "",
  decimals = 0,
  sub = "",
  delay = 0,
  trend = null,
}) {
  const numericValue = typeof value === "number" ? value : 0;
  const displayed = useCountUp(numericValue, 1400, decimals);
  const Icon = getIcon(iconName);

  const formatted =
    decimals > 0
      ? displayed.toFixed(decimals)
      : Math.round(displayed).toLocaleString();

  const TrendIcon = trend?.direction === "up"
    ? TrendingUp
    : trend?.direction === "down"
      ? TrendingDown
      : Minus;

  const trendColor = trend?.direction === "up"
    ? "var(--an-kpi-emerald)"
    : trend?.direction === "down"
      ? "var(--an-kpi-red)"
      : "var(--an-text-tertiary)";

  return (
    <motion.div
      className="an-kpi-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.45,
        delay,
        ease: [0.32, 0.72, 0, 1],
      }}
      whileHover={{
        y: -2,
        boxShadow: "var(--an-card-shadow-hover)",
        borderColor: "var(--an-card-border-hover)",
        transition: { duration: 0.2, ease: [0.32, 0.72, 0, 1] },
      }}
    >
      <div
        className="an-kpi-icon"
        style={{
          background: `var(${bgVar})`,
          color: `var(${colorVar})`,
        }}
      >
        {Icon && <Icon size={18} />}
      </div>

      <div className="an-kpi-body">
        <div className="an-kpi-value-row">
          <p className="an-kpi-value">
            {formatted}{suffix}
          </p>
          {trend && trend.direction !== "neutral" && (
            <motion.div
              className="an-kpi-trend"
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: delay + 0.3 }}
              style={{ color: trendColor }}
              title={`${trend.pct > 0 ? "+" : ""}${trend.pct}% vs last week`}
            >
              <TrendIcon size={14} />
              <span>{Math.abs(trend.pct)}%</span>
            </motion.div>
          )}
        </div>
        <p className="an-kpi-label">{label}</p>
      </div>

      {sub && <p className="an-kpi-sub">{sub}</p>}
    </motion.div>
  );
}