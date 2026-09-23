import React from 'react';
import { useAuth } from '../../context/AuthContext';
import DashboardError from './components/DashboardError';
import DashboardLoading from './components/DashboardLoading';
import DashboardOverview from './components/DashboardOverview';
import { useDashboardData } from './hooks/useDashboardData';
import './dashboard.css';

export default function DashboardFeature() {
  const { user } = useAuth();
  const { dashboardData, error, isLoading, refetch } = useDashboardData();

  if (isLoading) {
    return <DashboardLoading />;
  }

  if (error) {
    return <DashboardError error={error} onRetry={refetch} />;
  }

  return <DashboardOverview dashboardData={dashboardData} user={user} />;
}
