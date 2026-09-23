import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchSharedFiles } from '../services/sharedWithMeService';
import { events, EVENTS } from '../../../utils/events';

export function useSharedFiles() {
  const mounted = useRef(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const refetch = useCallback(async (silent = false) => {
    if (!silent && mounted.current) {
      setIsLoading(true);
      setError(null);
    }
    try {
      const next = await fetchSharedFiles();
      if (mounted.current) {
        setData(next);
        setError(null);
      }
    } catch (requestError) {
      if (mounted.current && !silent) {
        setError(requestError);
      }
    } finally {
      if (mounted.current && !silent) {
        setIsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    refetch(false);

    const unsub = events.on(EVENTS.NOTIFICATIONS_CHANGED, () => {
      refetch(true);
    });

    const handleFocus = () => {
      refetch(true);
    };
    window.addEventListener('focus', handleFocus);

    const interval = setInterval(() => {
      refetch(true);
    }, 15000);

    return () => {
      mounted.current = false;
      unsub();
      window.removeEventListener('focus', handleFocus);
      clearInterval(interval);
    };
  }, [refetch]);

  return { data, error, isLoading, refetch };
}