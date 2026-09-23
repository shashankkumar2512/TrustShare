// client/src/features/analytics/Analytics.js

import React, { useState, useEffect } from "react";
import { AnimatePresence } from "framer-motion";
import useAnalytics from "./hooks/useAnalytics";
import Header from "./components/Header/Header";
import { HeaderSkeleton } from "./components/shared/Skeleton";
import FileAnalyticsView from "./components/views/FileAnalyticsView";
import SecurityView from "./components/views/SecurityView";
import "./analytics.css";

const DATE_RANGE_TO_DAYS = {
  "7days":  7,
  "30days": 30,
  "90days": 90,
  "all":    365,
};

function parseCustomRange(value) {
  if (!value?.startsWith("custom-")) return null;
  const parts = value.replace("custom-", "").split("-to-");
  if (parts.length !== 2) return null;

  const start = new Date(parts[0]);
  const end   = new Date(parts[1]);

  // FIX ISS-4: Guard against invalid dates — prevents NaN being passed as days
  if (isNaN(start.getTime()) || isNaN(end.getTime())) return null;

  const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;
  return Math.max(1, Math.min(3650, days));  // FIX: cap aligned with API (3650)
}

export default function Analytics() {
  const [dateRange,    setDateRange]    = useState("30days");
  const [selectedUser, setSelectedUser] = useState("");

  const days = parseCustomRange(dateRange) ?? DATE_RANGE_TO_DAYS[dateRange] ?? 30;

  const {
    data,
    loading,
    error,
    refresh,
    autoRefreshEnabled,
    toggleAutoRefresh,
    lastRefreshedAt,
    nextRefreshIn,
  } = useAnalytics(days, selectedUser || null);

  const [activeTab, setActiveTab] = useState(() => {
    const saved = sessionStorage.getItem("analytics_active_tab");
    return saved === "security" ? "security" : "analytics";
  });

  const uiConfig = data?.ui_config;

  useEffect(() => {
    if (
      uiConfig?.tabs?.length &&
      !uiConfig.tabs.find((t) => t.value === activeTab)
    ) {
      setActiveTab(uiConfig.tabs[0].value);
    }
  }, [uiConfig, activeTab]);

  useEffect(() => {
    sessionStorage.setItem("analytics_active_tab", activeTab);
    window.dispatchEvent(
      new CustomEvent("analytics-tab-changed", {
        detail: activeTab,
      })
    );
  }, [activeTab]);

  if (error) {
    return (
      <div className="an-page">
        <div className="an-error">
          <p className="an-error-title">Unable to load analytics.</p>
          <button className="an-error-retry" onClick={refresh}>
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="an-page">
      {loading && !data ? (
        <HeaderSkeleton />
      ) : (
        <Header
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          data={data}
          uiConfig={uiConfig}
          dateRange={dateRange}
          setDateRange={setDateRange}
          onRefresh={refresh}
          autoRefreshEnabled={autoRefreshEnabled}
          toggleAutoRefresh={toggleAutoRefresh}
          lastRefreshedAt={lastRefreshedAt}
          nextRefreshIn={nextRefreshIn}
        />
      )}

      <AnimatePresence mode="wait">
        {activeTab === "analytics" ? (
          <FileAnalyticsView
            key="analytics"
            data={data}
            loading={loading}
            uiConfig={uiConfig}
          />
        ) : (
          <SecurityView
            key="security"
            data={data}
            loading={loading}
            uiConfig={uiConfig}
            selectedUser={selectedUser}
            onUserFilterChange={setSelectedUser}
          />
        )}
      </AnimatePresence>
    </div>
  );
}