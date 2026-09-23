// client/src/features/analytics/components/charts/StorageAreaChart.js

import React from "react";
import {
  AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { motion } from "framer-motion";
import Card, { CardHeader } from "../shared/Card";
import ChartTooltip from "./ChartTooltip";
import { AreaChartSkeleton } from "../shared/Skeleton";
import EmptyState from "../shared/EmptyState";
import useChartTheme from "../../hooks/useChartTheme";

export default function StorageAreaChart({
  trend = [],
  loading = false,
  config = {},
}) {
  const ct = useChartTheme();
  const gradId = "an-storage-grad";

  const title = config.title || "Storage Usage Over Time";
  const meta = config.meta || "";
  const xKey = config.x_key || "month";
  const dataKey = config.data_key || "gb";
  const valLabel = config.value_label || "Storage";

  const maxGb = Math.max(...trend.map((d) => d[dataKey] || 0), 0);
  const useMB = maxGb < 1 && maxGb > 0;

  const scaledData = trend.map((d) => ({
    ...d,
    [dataKey]: useMB ? +(d[dataKey] * 1024).toFixed(2) : d[dataKey],
  }));

  const unit = useMB ? " MB" : " GB";

  return (
    <Card delay={0.1} className="an-chart-card">
      <CardHeader
        title={title}
        right={meta && <span className="an-chart-meta">{meta}</span>}
      />

      {loading ? (
        <AreaChartSkeleton height={200} />
      ) : !trend.length ? (
        <EmptyState message="No storage trend data yet." />
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.15 }}
        >
          <ResponsiveContainer width="100%" height="100%" minHeight={200}>
            <AreaChart
              data={scaledData}
              margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={ct.storageStroke} stopOpacity={0.18} />
                  <stop offset="95%" stopColor={ct.storageStroke} stopOpacity={0.01} />
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" stroke={ct.gridStroke} />

              <XAxis
                dataKey={xKey}
                tick={{ fontSize: ct.axisTickFontSize, fill: ct.axisTickFill }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: ct.axisTickFontSize, fill: ct.axisTickFill }}
                axisLine={false}
                tickLine={false}
                unit={unit}
              />
              <Tooltip content={<ChartTooltip />} />

              <Area
                type="monotone"
                dataKey={dataKey}
                name={`${valLabel} (${unit.trim()})`}
                stroke={ct.storageStroke}
                strokeWidth={2.5}
                fill={`url(#${gradId})`}
                dot={{ fill: ct.storageDotFill, r: 4, strokeWidth: 0 }}
                activeDot={{ r: 5 }}
                animationDuration={1200}
                animationEasing="ease-out"
              />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>
      )}
    </Card>
  );
}