// client/src/features/analytics/components/views/SecurityView.js

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import KPIGrid from "../kpi/KPIGrid";
import LoginLineChart from "../charts/LoginLineChart";
import SecurityTimeline from "../panels/SecurityTimeline";
import UnauthorizedTable from "../panels/UnauthorizedTable";
import RecentActivityPanel from "../panels/RecentActivityPanel";
import SystemHealthPanel from "../panels/SystemHealthPanel";
import { analyticsAPI } from "../../../../utils/api";

import SecurityScoreGauge from "../panels/SecurityScoreGauge";
import FailedLoginHeatmap from "../charts/FailedLoginHeatmap";
import MFAAdoptionCard from "../panels/MFAAdoptionCard";
import PerformancePanel from "../panels/PerformancePanel";

const SECURITY_KPI_SKELETON_COUNT = 4;

export default function SecurityView({
  data,
  loading,
  uiConfig,
  selectedUser,
  onUserFilterChange,
}) {
  const [users, setUsers] = useState([]);

  const kpiConfig = uiConfig?.security_kpis || [];
  const chartsCfg = uiConfig?.charts || {};
  const panelsCfg = uiConfig?.panels || {};
  const severity = uiConfig?.severity || {};

  const isAdmin = data?.current_user_role === "admin";

  useEffect(() => {
    if (!isAdmin) {
      setUsers([]);
      return;
    }

    analyticsAPI
      .users()
      .then((r) => setUsers(r.data.users || []))
      .catch(() => setUsers([]));
  }, [isAdmin]);

  const kpiData = {
    login_events: data?.security?.login_events ?? 0,
    failed_logins: data?.security?.failed_logins ?? 0,
    blocked_attacks: data?.security?.blocked_attacks ?? 0,
    security_events: data?.security?.security_events ?? 0,
  };

  return (
    <motion.div
      className="an-view"
      key="security"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25, ease: "easeInOut" }}
    >
      <KPIGrid
        config={kpiConfig}
        data={kpiData}
        kpiTrends={data?.kpiTrends || {}}
        skeletonCount={SECURITY_KPI_SKELETON_COUNT}
        loading={loading}
      />

      <div className="an-row an-row--3-2">
        <SecurityScoreGauge
          scoreData={data?.security_score}
          loading={loading}
          config={panelsCfg.security_score}
        />
        <MFAAdoptionCard
          mfaData={data?.mfa_adoption}
          loading={loading}
          config={panelsCfg.mfa_adoption}
        />
      </div>

      <div className="an-row an-row--3-2">
        <LoginLineChart
          loginActivity={data?.security?.login_activity}
          loading={loading}
          config={chartsCfg.login}
        />
        <SecurityTimeline
          events={data?.security?.events}
          loading={loading}
          config={panelsCfg.timeline}
          severity={severity}
        />
      </div>

      <div className="an-row an-row--1">
        <FailedLoginHeatmap
          heatmapData={data?.failed_login_heatmap}
          loading={loading}
          config={chartsCfg.login_heatmap}
        />
      </div>

      <UnauthorizedTable
        attempts={data?.security?.unauthorized_attempts}
        loading={loading}
        config={panelsCfg.unauthorized}
      />

      <div className="an-row an-row--3-2">
        <RecentActivityPanel
          activities={data?.recent_activity?.activities}
          loading={loading}
          config={panelsCfg.recent_activity}
          users={users}
          selectedUser={selectedUser}
          onUserChange={onUserFilterChange}
        />
        <SystemHealthPanel
          stats={data?.system_stats}
          loading={loading}
          config={panelsCfg.system_stats}
        />
      </div>
      <div className="an-row an-row--1">
        <PerformancePanel
          performanceData={data?.performance_metrics}
          loading={loading}
        />
      </div>
    </motion.div>
  );
}