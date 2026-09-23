import React from 'react';

export default function DashboardLoading() {
  return (
    <div aria-label="Loading dashboard" className="dashboard-loading" role="status">
      <div className="dashboard-skeleton dashboard-skeleton-header" />
      <div className="dashboard-loading-grid">
        {[0, 1, 2, 3].map((item) => (
          <div className="dashboard-skeleton dashboard-skeleton-card" key={item} />
        ))}
      </div>
      <div className="dashboard-skeleton dashboard-skeleton-panel" />
      <span className="sr-only">Loading dashboard data</span>
    </div>
  );
}
