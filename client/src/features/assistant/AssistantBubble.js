import React, { useState, useCallback, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import { Sparkles } from 'lucide-react';
import { useAssistantStatus } from './hooks/useAssistantStatus';
import { useAuth } from '../../context/AuthContext';
import { assistantAPI } from './services/assistantAPI';
import AssistantBubbleWindow from './AssistantBubbleWindow';
import './assistant.css';

const BUBBLE_CONV_KEY = 'trustshare_bubble_conversation_id';

const AssistantBubble = () => {
    const { status } = useAssistantStatus();
    const { user } = useAuth();
    const location = useLocation();

    const [open, setOpen] = useState(false);

    const [bubbleConversationId, setBubbleConversationId] = useState(() => {
        try {
            const saved = sessionStorage.getItem(BUBBLE_CONV_KEY);
            return saved ? parseInt(saved, 10) : null;
        } catch {
            return null;
        }
    });

    useEffect(() => {
        try {
            if (bubbleConversationId) {
                sessionStorage.setItem(BUBBLE_CONV_KEY, String(bubbleConversationId));
            } else {
                sessionStorage.removeItem(BUBBLE_CONV_KEY);
            }
        } catch {
        }
    }, [bubbleConversationId]);

    useEffect(() => {
        setOpen(false);
    }, [location.pathname]);

    useEffect(() => {
        if (!open) return;

        const handleClickOutside = (e) => {
            const isInsideWindow = e.target.closest('.asst-bubble-window');
            const isOnBubble = e.target.closest('.asst-bubble');

            if (!isInsideWindow && !isOnBubble) {
                setOpen(false);
            }
        };

        const timer = setTimeout(() => {
            document.addEventListener('mousedown', handleClickOutside);
        }, 100);

        return () => {
            clearTimeout(timer);
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [open]);

    useEffect(() => {
        if (!user) {
            setBubbleConversationId(null);
            setOpen(false);
            try {
                sessionStorage.removeItem(BUBBLE_CONV_KEY);
                sessionStorage.removeItem('trustshare_bubble_open');
            } catch {

            }
        }
    }, [user]);

    useEffect(() => {
        if (!user || !bubbleConversationId) return;

        let cancelled = false;

        (async () => {
            try {
                await assistantAPI.getMessages(bubbleConversationId);
            } catch (err) {
                if (cancelled) return;
                const status = err?.response?.status;
                if (status === 404 || status === 403 || status === 401) {
                    console.log('[Bubble] Clearing stale conversation ID:', bubbleConversationId);
                    setBubbleConversationId(null);
                }
            }
        })();

        return () => {
            cancelled = true;
        };
    }, [user]);

    const handleConversationCreated = useCallback((newId) => {
        setBubbleConversationId(newId);
    }, []);

    const handleNewChat = useCallback(() => {
        setBubbleConversationId(null);
    }, []);

    const handleConversationNotFound = useCallback(() => {
        console.log('[Bubble] Conversation not found, resetting to new chat');
        setBubbleConversationId(null);
    }, []);

    const handleOpen = useCallback(() => {
        setOpen(true);
    }, []);

    const handleClose = useCallback(() => {
        setOpen(false);
    }, []);

    // Don't render bubble if disabled or user not loaded
    if (!status || !status.is_enabled || !status.show_bubble) {
        return null;
    }

    if (!user) {
        return null;
    }

    return (
        <>
            <AnimatePresence>
                {!open && (
                    <motion.button
                        className="asst-bubble"
                        onClick={handleOpen}
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: [0.32, 0.72, 0, 1] }}
                        aria-label="Open AI Assistant"
                    >
                        <Sparkles size={22} />
                    </motion.button>
                )}
            </AnimatePresence>

            <AnimatePresence>
                {open && (
                    <AssistantBubbleWindow
                        status={status}
                        onClose={handleClose}
                        conversationId={bubbleConversationId}
                        onConversationCreated={handleConversationCreated}
                        onNewChat={handleNewChat}
                        onConversationNotFound={handleConversationNotFound}
                    />
                )}
            </AnimatePresence>
        </>
    );
};

export default AssistantBubble;