import { useState, useEffect, useCallback } from 'react';
import { assistantAPI } from '../services/assistantAPI';

export function useConversations() {
    const [conversations, setConversations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchConversations = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const { data } = await assistantAPI.listConversations();
            setConversations(data || []);
        } catch (err) {
            const msg = err?.response?.data?.detail || err?.message || 'Failed to load conversations';
            setError(msg);
        } finally {
            setLoading(false);
        }
    }, []);

    const archive = useCallback(async (conversationId) => {
        try {
            await assistantAPI.archiveConversation(conversationId);
            setConversations((prev) => prev.filter((c) => c.id !== conversationId));
            return true;
        } catch (err) {
            const msg = err?.response?.data?.detail || err?.message || 'Failed to archive';
            setError(msg);
            return false;
        }
    }, []);

    const rename = useCallback(async (conversationId, newTitle) => {
        try {
            const { data } = await assistantAPI.renameConversation(conversationId, newTitle);
            setConversations((prev) =>
                prev.map((c) => (c.id === conversationId ? { ...c, title: data.title } : c))
            );
            return true;
        } catch (err) {
            const msg = err?.response?.data?.detail || err?.message || 'Failed to rename';
            setError(msg);
            return false;
        }
    }, []);

    useEffect(() => {
        fetchConversations();
    }, [fetchConversations]);

    return {
        conversations,
        loading,
        error,
        refetch: fetchConversations,
        archive,
        rename,
    };
}