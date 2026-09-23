// client/src/features/analytics/hooks/useAnalytics.js

import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";  // ← ADD THIS IMPORT
import { getAnalyticsSummary } from "../services/analyticsService";

function formatStorageValue(gb) {
  if (gb < 1) return { value: gb * 1024, unit: " MB", decimals: 1 };
  return { value: gb, unit: " GB", decimals: 1 };
}

function formatTransferred(gb, mb) {
  if (gb >= 1) return `${gb} GB transferred`;
  if (mb >= 1) return `${mb} MB transferred`;
  return "< 1 MB transferred";
}

function formatChange(pct) {
  if (pct > 0) return `+${pct}% vs last`;
  if (pct < 0) return `${pct}% vs last`;
  return "same as last";
}

// Simple cache to prevent re-fetching on tab switch
const cache = {};
function getCacheKey(days, userId) {
  return `${days}-${userId || "all"}`;
}

// ═══ Auto-refresh interval (30 seconds) ═══
const AUTO_REFRESH_INTERVAL = 30000;

export default function useAnalytics(days = 30, userId = null) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // ═══ Auto-refresh state ═══
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);
  const [lastRefreshedAt, setLastRefreshedAt] = useState(null);
  const [nextRefreshIn, setNextRefreshIn] = useState(AUTO_REFRESH_INTERVAL / 1000);

  const intervalRef  = useRef(null);
  const countdownRef = useRef(null);
  const isMountedRef = useRef(true);

  // ═══ FIX: Track route to detect navigation back to analytics ═══
  const location = useLocation();

  const fetchData = useCallback(async (forceRefresh = false, silent = false) => {
    const key = getCacheKey(days, userId);

    // Use cache if available and not force refreshing (within 60 seconds)
    if (!forceRefresh && cache[key] && Date.now() - cache[key].time < 60000) {
      if (isMountedRef.current) {
        setData(cache[key].data);
        setLoading(false);
        setLastRefreshedAt(cache[key].time);
      }
      return;
    }

    try {
      if (!silent && isMountedRef.current) {
        setLoading(true);
      }
      if (isMountedRef.current) {
        setError(null);
      }

      const result = await getAnalyticsSummary(days, userId);

      const s   = result.storage;
      const u   = result.uploads;
      const d   = result.downloads;
      const del = result.deletes;
      const sh  = result.sharing;
      const trends = result.trends || {};

      const storageGB  = s?.storage_used_gb ?? 0;
      const storageFmt = formatStorageValue(storageGB);

      // Dynamic KPI overrides
      if (result.ui_config?.file_kpis) {
        result.ui_config = {
          ...result.ui_config,
          file_kpis: result.ui_config.file_kpis.map((kpi) =>
            kpi.key === "storage"
              ? { ...kpi, suffix: storageFmt.unit, decimals: storageFmt.decimals }
              : kpi
          ),
        };
      }

      // Subtitles from real DB data
      const storageSub   = `of ${s?.storage_quota_gb ?? 0} GB · ${(s?.storage_percentage ?? 0).toFixed(1)}% capacity`;
      const uploadsSub   = `this month · ${formatChange(u?.change_pct ?? 0)}`;
      const downloadsSub = `this month · ${formatTransferred(d?.transferred_gb ?? 0, d?.transferred_mb ?? 0)}`;
      const sharesSub    = (sh?.new_this_week ?? 0) > 0
        ? `+${sh.new_this_week} new this week`
        : `${sh?.inactive_links ?? 0} inactive`;
      const deletesSub   = (del?.this_week_deletes ?? 0) > 0
        ? `${del.this_week_deletes} this week`
        : `${del?.this_month_deletes ?? 0} this month`;

      const trendData = trends?.trends || {};

      const enriched = {
        ...result,
        kpi: {
          storage:   storageFmt.value,
          uploads:   u?.total_uploads   ?? 0,
          downloads: d?.total_downloads ?? 0,
          shares:    sh?.active_links   ?? 0,
          deletes:   del?.total_deletes ?? 0,
        },
        subtitles: {
          storage_subtitle:   storageSub,
          uploads_subtitle:   uploadsSub,
          downloads_subtitle: downloadsSub,
          shares_subtitle:    sharesSub,
          deletes_subtitle:   deletesSub,
        },
        kpiTrends: {
          uploads:   trendData.uploads   || null,
          downloads: trendData.downloads || null,
          shares:    trendData.shares    || null,
          logins:    trendData.logins    || null,
          failed:    trendData.failed    || null,
        },
        fileAccessHistory: trends?.file_access_history || [],
      };

      // Cache the result
      const fetchTime = Date.now();
      cache[key] = { data: enriched, time: fetchTime };

      if (isMountedRef.current) {
        setLastRefreshedAt(fetchTime);
        setNextRefreshIn(AUTO_REFRESH_INTERVAL / 1000);
        setData(enriched);
      }
    } catch (err) {
      console.error("[useAnalytics] error:", err);
      if (isMountedRef.current) {
        setError(err);
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [days, userId]);

  // ═══ Mount / unmount tracking ════════════════════════════════════════
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // ═══ Initial fetch ════════════════════════════════════════════════════
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // ═══ FIX: Refresh when user navigates back to analytics page ═════════
  // Fires every time the route changes TO /analytics.
  // Clears cache so fresh data is always fetched on navigation.
  // silent=true so no loading spinner shows — seamless experience.
  useEffect(() => {
    if (
      location.pathname === "/analytics" &&
      isMountedRef.current
    ) {
      const key = getCacheKey(days, userId);
      delete cache[key]; // always clear cache on navigation to analytics
      fetchData(true, true); // forceRefresh=true, silent=true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]); // only fires when pathname changes

  // ═══ Force refresh (bypasses cache) ══════════════════════════════════
  const refresh = useCallback(() => {
    const key = getCacheKey(days, userId);
    delete cache[key];
    setNextRefreshIn(AUTO_REFRESH_INTERVAL / 1000);
    return fetchData(true, false); // Not silent — show loading
  }, [fetchData, days, userId]);

  // ═══ Auto-refresh interval + countdown ═══════════════════════════════
  useEffect(() => {
    // Clean up existing intervals
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
      countdownRef.current = null;
    }

    if (!autoRefreshEnabled) {
      setNextRefreshIn(AUTO_REFRESH_INTERVAL / 1000);
      return;
    }

    countdownRef.current = setInterval(() => {
      if (!isMountedRef.current) return;
      setNextRefreshIn((prev) => {
        if (prev <= 1) return AUTO_REFRESH_INTERVAL / 1000;
        return prev - 1;
      });
    }, 1000);

    intervalRef.current = setInterval(() => {
      if (!isMountedRef.current) return;
      const key = getCacheKey(days, userId);
      delete cache[key];
      fetchData(true, true);
    }, AUTO_REFRESH_INTERVAL);

    // Cleanup on unmount or dependency change
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      if (countdownRef.current) {
        clearInterval(countdownRef.current);
        countdownRef.current = null;
      }
    };
  }, [autoRefreshEnabled, days, userId, fetchData]);

  // ═══ Toggle auto-refresh ══════════════════════════════════════════════
  const toggleAutoRefresh = useCallback(() => {
    setAutoRefreshEnabled((prev) => !prev);
  }, []);

  return {
    data,
    loading,
    error,
    refresh,
    autoRefreshEnabled,
    toggleAutoRefresh,
    lastRefreshedAt,
    nextRefreshIn,
  };
}