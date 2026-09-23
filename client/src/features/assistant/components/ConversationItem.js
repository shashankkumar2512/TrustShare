import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Trash2, MessageCircle } from 'lucide-react';

const formatDate = (iso) => {
    if (!iso) return '';
    try {
        const d = new Date(iso);
        const now = new Date();
        const diffMs = now - d;
        const diffMin = Math.floor(diffMs / 60000);
        const diffHr = Math.floor(diffMin / 60);
        const diffDay = Math.floor(diffHr / 24);

        if (diffMin < 1) return 'now';
        if (diffMin < 60) return `${diffMin}m`;
        if (diffHr < 24) return `${diffHr}h`;
        if (diffDay < 7) return `${diffDay}d`;
        return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    } catch {
        return '';
    }
};

const ConversationItem = ({ conversation, isActive, onSelect, onDelete, onRename }) => {
    const [renaming, setRenaming] = useState(false);
    const [newTitle, setNewTitle] = useState(conversation.title || '');
    const inputRef = useRef(null);

    useEffect(() => {
        if (renaming && inputRef.current) {
            inputRef.current.focus();
            inputRef.current.select();
        }
    }, [renaming]);

    const handleDelete = (e) => {
        e.stopPropagation();
        if (window.confirm('Delete this conversation?')) {
            onDelete(conversation.id);
        }
    };

    const handleDoubleClick = (e) => {
        e.stopPropagation();
        if (!onRename) return;
        setNewTitle(conversation.title || '');
        setRenaming(true);
    };

    const handleRenameSubmit = async () => {
        const trimmed = newTitle.trim();
        if (trimmed && trimmed !== conversation.title && onRename) {
            await onRename(conversation.id, trimmed);
        }
        setRenaming(false);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleRenameSubmit();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            setRenaming(false);
        }
    };

    return (
        <motion.button
            className={`asst-conv-item ${isActive ? 'active' : ''}`}
            onClick={() => !renaming && onSelect(conversation.id)}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            whileHover={{ x: renaming ? 0 : 2 }}
            transition={{ duration: 0.2 }}
        >
            <MessageCircle size={14} style={{ flexShrink: 0, opacity: 0.7 }} />

            {renaming ? (
                <input
                    ref={inputRef}
                    className="asst-conv-rename-input"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    onBlur={handleRenameSubmit}
                    onKeyDown={handleKeyDown}
                    onClick={(e) => e.stopPropagation()}
                    maxLength={200}
                />
            ) : (
                <>
                    <span
                        className="asst-conv-title"
                        onDoubleClick={handleDoubleClick}
                        title="Double-click to rename"
                    >
                        {conversation.title || 'New Conversation'}
                    </span>
                    <span className="asst-conv-meta">
                        {formatDate(conversation.updated_at)}
                    </span>
                    <span
                        className="asst-conv-delete"
                        onClick={handleDelete}
                        role="button"
                        tabIndex={-1}
                        aria-label="Delete conversation"
                    >
                        <Trash2 size={13} />
                    </span>
                </>
            )}
        </motion.button>
    );
};

export default ConversationItem;