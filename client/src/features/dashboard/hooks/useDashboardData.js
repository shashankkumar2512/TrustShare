import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchDashboardData } from '../services/dashboardService';

export function useDashboardData() {
  const isMounted = useRef(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    isMounted.current = true;

    return () => {
      isMounted.current = false;
    };
  }, []);

  const loadDashboard = useCallback(async () => {
    if (isMounted.current) {
      setIsLoading(true);
      setError(null);
    }

    try {
      const data = await fetchDashboardData();
      if (isMounted.current) {
        setDashboardData(data);
      }
    } catch (requestError) {
      if (isMounted.current) {
        setDashboardData(null);
        setError(requestError);
      }
    } finally {
      if (isMounted.current) {
        setIsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  return {
    dashboardData,
    error,
    isLoading,
    refetch: loadDashboard,
  };
}
