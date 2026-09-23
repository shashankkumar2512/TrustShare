import React, { useState } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Sparkles, AlertCircle, Copy, Check, RotateCcw } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import ResultCardRouter from './result-cards/ResultCardRouter';

const getInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase();
};

const formatTime = (iso) => {
    if (!iso) return '';
    try {
        return new Date(iso).toLocaleTimeString(undefined, {
            hour: '2-digit',
            minute: '2-digit',
        });
    } catch {
        return '';
    }
};

const MessageBubble = ({
    message,
    onRegenerate,
    canRegenerate = false,
    enableMarkdown = true,
    showTokenUsage = false,
    isLast = false,
}) => {
    const { user } = useAuth();
    const [copied, setCopied] = useState(false);
    const { role, content, function_name, function_result, isError, model_used, tokens_used, created_at } = message;

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(content || '');
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch {
            // Fallback for older browsers
        }
    };

    if (role === 'function') {
        return (
            <motion.div
                className="asst-msg-row assistant"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: [0.32, 0.72, 0, 1] }}
            >
                <div className="asst-msg-avatar assistant">
                    <Sparkles size={16} />
                </div>
                <div className="asst-msg-content" style={{ maxWidth: '85%' }}>
                    <ResultCardRouter
                        functionName={function_name}
                        result={function_result}
                    />
                </div>
            </motion.div>
        );
    }

    const isUser = role === 'user';
    const showActions = !isUser && !isError && content;

    return (
        <motion.div
            className={`asst-msg-row ${isUser ? 'user' : 'assistant'}`}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: [0.32, 0.72, 0, 1] }}
        >
            <div className={`asst-msg-avatar ${isUser ? 'user' : 'assistant'}`}>
                {isUser ? getInitials(user?.name) : <Sparkles size={16} />}
            </div>
            <div className="asst-msg-content">
                <div
                    className={`asst-msg-bubble ${isUser ? 'user' : 'assistant'} ${isError ? 'error' : ''}`}
                    title={created_at ? formatTime(created_at) : ''}
                >
                    {isError && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, fontWeight: 600 }}>
                            <AlertCircle size={16} />
                            <span>Error</span>
                        </div>
                    )}
                    {enableMarkdown && !isError ? (
                        <div className="asst-markdown">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {content || ''}
                            </ReactMarkdown>
                        </div>
                    ) : (
                        content
                    )}
                </div>

                {/* Meta row: model + tokens + actions */}
                {(model_used || showActions) && !isUser && (
                    <div className="asst-msg-meta">
                        {model_used && (
                            <>
                                <Sparkles size={10} />
                                <span>{model_used}</span>
                            </>
                        )}
                        {showTokenUsage && tokens_used && (
                            <span className="asst-token-badge">
                                {tokens_used} tokens
                            </span>
                        )}
                    </div>
                )}

                {/* Action buttons */}
                {showActions && (
                    <div className="asst-msg-actions">
                        <button
                            className={`asst-msg-action-btn ${copied ? 'copied' : ''}`}
                            onClick={handleCopy}
                            title="Copy to clipboard"
                        >
                            {copied ? <Check size={12} /> : <Copy size={12} />}
                            {copied ? 'Copied' : 'Copy'}
                        </button>
                        {isLast && canRegenerate && onRegenerate && (
                            <button
                                className="asst-msg-action-btn"
                                onClick={onRegenerate}
                                title="Regenerate response"
                            >
                                <RotateCcw size={12} />
                                Regenerate
                            </button>
                        )}
                    </div>
                )}
            </div>
        </motion.div>
    );
};

export default MessageBubble;