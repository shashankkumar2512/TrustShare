import { useState, useEffect, useMemo } from 'react';
import { assistantAPI } from '../services/assistantAPI';

export function useSuggestions() {
    const [flat, setFlat] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const { data } = await assistantAPI.getSuggestions();
                if (!cancelled) {
                    setFlat(data || []);
                }
            } catch (err) {
                if (!cancelled) {
                    const msg = err?.response?.data?.detail || err?.message || 'Failed to load suggestions';
                    setError(msg);
                }
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();

        return () => {
            cancelled = true;
        };
    }, []);

    const grouped = useMemo(() => {
        const map = {};
        flat.forEach((q) => {
            if (!map[q.category]) map[q.category] = [];
            map[q.category].push(q);
        });
        return map;
    }, [flat]);

    return { grouped, flat, loading, error };
}