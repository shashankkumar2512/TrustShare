import { useState, useEffect, useCallback, useRef } from 'react';
import { assistantAPI } from '../services/assistantAPI';

export function useChat(initialConversationId = null) {
    const [conversationId, setConversationId] = useState(initialConversationId);
    const [messages, setMessages] = useState([]);
    const [sending, setSending] = useState(false);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [error, setError] = useState(null);

    const lastUserMessageRef = useRef(null);
    const isMountedRef = useRef(true);
    const isInitialLoadDoneRef = useRef(false);

    useEffect(() => {
        isMountedRef.current = true;
        return () => { isMountedRef.current = false; };
    }, []);

    useEffect(() => {
        // Reset for new conversation
        isInitialLoadDoneRef.current = false;
        setConversationId(initialConversationId);
    }, [initialConversationId]);

    useEffect(() => {
        if (!conversationId) {
            setMessages([]);
            isInitialLoadDoneRef.current = false;
            return;
        }
        if (isInitialLoadDoneRef.current) {
            return;
        }

        let cancelled = false;
        (async () => {
            setLoadingHistory(true);
            setError(null);
            try {
                const { data } = await assistantAPI.getMessages(conversationId);
                if (!cancelled && isMountedRef.current) {
                    setMessages(data || []);
                    isInitialLoadDoneRef.current = true;
                }
            } catch (err) {
                if (!cancelled && isMountedRef.current) {
                    setError(err?.response?.data?.detail || err?.message || 'Failed to load');
                }
            } finally {
                if (!cancelled && isMountedRef.current) {
                    setLoadingHistory(false);
                }
            }
        })();

        return () => { cancelled = true; };
    }, [conversationId]);

    const _extractErrorMessage = (err) => {
        const s = err?.response?.status;
        const d = err?.response?.data?.detail;
        if (s === 429) return "🚫 Too many requests. Wait a moment.";
        if (s === 401) return '🔑 Session expired.';
        if (s === 403) return "🔒 Permission denied.";
        if (s >= 500) return '⚠️ Server error.';
        if (err?.code === 'ERR_NETWORK') return '🌐 Network error.';
        return d?.message || (typeof d === 'string' ? d : null) || err?.message || 'Failed.';
    };

    const sendMessage = useCallback(
        async (text) => {
            const trimmed = text.trim();
            if (!trimmed || sending) return;

            const sendConvId = conversationId;
            lastUserMessageRef.current = trimmed;
            setError(null);
            setSending(true);

            const userMsgId = `u-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
            setMessages((prev) => [...prev, {
                id: userMsgId,
                role: 'user',
                content: trimmed,
                created_at: new Date().toISOString(),
            }]);

            try {
                const { data } = await assistantAPI.sendMessage(trimmed, sendConvId);

                if (!isMountedRef.current) return;

                if (data.error) {
                    setMessages((prev) => [...prev, {
                        id: `e-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
                        role: 'assistant',
                        content: data.message || 'Error',
                        created_at: new Date().toISOString(),
                        isError: true,
                    }]);
                    return;
                }

                if (data.conversation_id && data.conversation_id !== sendConvId) {
                    isInitialLoadDoneRef.current = true;
                    setConversationId(data.conversation_id);
                }

                const newMsgs = [];

                if (data.function_calls && data.function_calls.length > 0) {
                    data.function_calls.forEach((fc) => {
                        newMsgs.push({
                            id: `f-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
                            role: 'function',
                            function_name: fc.name,
                            function_result: fc.result,
                            created_at: new Date().toISOString(),
                        });
                    });
                }

                newMsgs.push({
                    id: `a-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
                    role: 'assistant',
                    content: data.message,
                    tokens_used: data.tokens_used,
                    model_used: data.model_used,
                    created_at: new Date().toISOString(),
                });

                setMessages((prev) => [...prev, ...newMsgs]);

            } catch (err) {
                if (!isMountedRef.current) return;
                if (err.name === 'AbortError' || err.name === 'CanceledError') return;

                setMessages((prev) => [...prev, {
                    id: `e-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
                    role: 'assistant',
                    content: _extractErrorMessage(err),
                    created_at: new Date().toISOString(),
                    isError: true,
                }]);

            } finally {
                if (isMountedRef.current) setSending(false);
            }
        },
        [conversationId, sending]
    );

    const regenerateLastMessage = useCallback(async () => {
        if (!lastUserMessageRef.current) return;
        setMessages((prev) => {
            const msgs = [...prev];
            while (msgs.length > 0 && msgs[msgs.length - 1].role !== 'user') msgs.pop();
            return msgs;
        });
        await new Promise((r) => setTimeout(r, 50));

        const text = lastUserMessageRef.current;
        lastUserMessageRef.current = null;
        await sendMessage(text);
    }, [sendMessage]);

    const stopGenerating = useCallback(() => {
        setSending(false);
    }, []);

    const resetChat = useCallback(() => {
        setConversationId(null);
        setMessages([]);
        setError(null);
        lastUserMessageRef.current = null;
        isInitialLoadDoneRef.current = false;
    }, []);

    return {
        messages,
        sending,
        loadingHistory,
        error,
        sendMessage,
        regenerateLastMessage,
        stopGenerating,
        resetChat,
        conversationId,
        canRegenerate: !!lastUserMessageRef.current && !sending,
    };
}