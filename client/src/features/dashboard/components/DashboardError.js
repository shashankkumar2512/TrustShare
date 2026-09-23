import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function DashboardError({ error, onRetry }) {
  const message =
    error?.response?.data?.detail ||
    error?.message ||
    'The dashboard could not be loaded.';

  return (
    <section className="dashboard-error" role="alert">
      <span className="dashboard-error-icon">
        <AlertTriangle aria-hidden="true" size={28} />
      </span>
      <h1>Unable to load dashboard</h1>
      <p>{message}</p>
      <button className="btn btn-primary" onClick={onRetry} type="button">
        <RefreshCw aria-hidden="true" size={16} />
        Retry
      </button>
    </section>
  );
}
