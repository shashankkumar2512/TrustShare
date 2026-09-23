import { useState, useEffect, useCallback } from 'react';
import { assistantAPI } from '../services/assistantAPI';

export function useAssistantStatus() {
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchStatus = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const { data } = await assistantAPI.getStatus();
            setStatus(data);
        } catch (err) {
            const msg = err?.response?.data?.detail || err?.message || 'Failed to load assistant status';
            setError(msg);
            setStatus(null);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchStatus();
    }, [fetchStatus]);

    return { status, loading, error, refetch: fetchStatus };
}