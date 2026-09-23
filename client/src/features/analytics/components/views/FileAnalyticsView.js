// client/src/features/analytics/components/views/FileAnalyticsView.js

import React from "react";
import { motion } from "framer-motion";
import KPIGrid from "../kpi/KPIGrid";
import StorageAreaChart from "../charts/StorageAreaChart";
import VolumeBarChart from "../charts/VolumeBarChart";
import DepartmentDonut from "../charts/DepartmentDonut";
import TopSharedFiles from "../panels/TopSharedFiles";
import FileTypeDonut from "../charts/FileTypeDonut";
import TopActiveUsers from "../panels/TopActiveUsers";
import PerformancePanel from "../panels/PerformancePanel";

const FILE_KPI_SKELETON_COUNT = 5;

export default function FileAnalyticsView({ data, loading, uiConfig }) {
  const kpiConfig = uiConfig?.file_kpis || [];
  const chartsCfg = uiConfig?.charts || {};
  const panelsCfg = uiConfig?.panels || {};
  const isAdmin = data?.current_user_role === "admin";

  return (
    <motion.div
      className="an-view"
      key="file-analytics"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25, ease: "easeInOut" }}
    >
      <KPIGrid
        config={kpiConfig}
        data={data?.kpi}
        subtitles={data?.subtitles}
        kpiTrends={data?.kpiTrends || {}}
        skeletonCount={FILE_KPI_SKELETON_COUNT}
        loading={loading}
      />

      <div className="an-row an-row--3-2">
        <StorageAreaChart
          trend={data?.storage?.trend}
          loading={loading}
          config={chartsCfg.storage}
        />
        <TopSharedFiles
          topFiles={data?.sharing?.top_files}
          loading={loading}
          config={panelsCfg.top_files}
        />
      </div>

      {isAdmin ? (
        <div className="an-row an-row--3-2">
          <VolumeBarChart
            volumeWeekly={data?.uploads?.volume_weekly}
            loading={loading}
            config={chartsCfg.volume}
          />
          <DepartmentDonut
            byDepartment={data?.sharing?.by_department}
            loading={loading}
            config={chartsCfg.department}
          />
        </div>
      ) : (
        <div className="an-row an-row--1">
          <VolumeBarChart
            volumeWeekly={data?.uploads?.volume_weekly}
            loading={loading}
            config={chartsCfg.volume}
          />
        </div>
      )}

      <div className="an-row an-row--3-2">
        <FileTypeDonut
          fileTypes={data?.file_types}
          loading={loading}
          config={chartsCfg.file_types}
        />
        <TopActiveUsers
          users={data?.top_active_users}
          loading={loading}
          config={panelsCfg.top_active_users}
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