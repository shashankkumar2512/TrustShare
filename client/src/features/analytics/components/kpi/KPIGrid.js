// client/src/features/analytics/components/kpi/KPIGrid.js

import React from "react";
import KPICard from "./KPICard";
import { KPIGridSkeleton } from "../shared/Skeleton";

const TREND_KEY_MAP = {
  uploads: "uploads",
  downloads: "downloads",
  shares: "shares",
  login_events: "logins",
  failed_logins: "failed",
};

export default function KPIGrid({
  config = [],
  data = {},
  subtitles = {},
  kpiTrends = {},
  skeletonCount = 4,
  loading = false,
}) {
  if (loading) {
    return (
      <KPIGridSkeleton count={skeletonCount || config.length || 4} />
    );
  }

  return (
    <div className="an-kpi-grid">
      {config.map((cfg, i) => {
        const trendKey = TREND_KEY_MAP[cfg.key];
        const trend = trendKey ? kpiTrends[trendKey] : null;

        return (
          <KPICard
            key={cfg.key}
            delay={i * 0.06}
            iconName={cfg.icon}
            colorVar={cfg.color_var}
            bgVar={cfg.bg_var}
            label={cfg.label}
            value={data?.[cfg.key] ?? 0}
            suffix={cfg.suffix ?? ""}
            decimals={cfg.decimals ?? 0}
            sub={subtitles?.[cfg.sub_key] ?? ""}
            trend={trend}
          />
        );
      })}
    </div>
  );
}