import React, { useState, useMemo } from 'react';
import { Plus, Search } from 'lucide-react';
import ConversationItem from './ConversationItem';

const groupByDate = (conversations) => {
    const today = new Date();
    const yesterday = new Date();
    yesterday.setDate(today.getDate() - 1);
    const weekAgo = new Date();
    weekAgo.setDate(today.getDate() - 7);

    const groups = { today: [], yesterday: [], thisWeek: [], older: [] };

    conversations.forEach((c) => {
        const d = new Date(c.updated_at);
        if (d.toDateString() === today.toDateString()) {
            groups.today.push(c);
        } else if (d.toDateString() === yesterday.toDateString()) {
            groups.yesterday.push(c);
        } else if (d >= weekAgo) {
            groups.thisWeek.push(c);
        } else {
            groups.older.push(c);
        }
    });

    return groups;
};

const ConversationSidebar = ({
    conversations = [],
    activeId,
    onSelect,
    onDelete,
    onRename,  // NEW
    onNewChat,
}) => {
    const [search, setSearch] = useState('');

    const filtered = useMemo(() => {
        if (!search.trim()) return conversations;
        const q = search.toLowerCase();
        return conversations.filter((c) =>
            (c.title || '').toLowerCase().includes(q)
        );
    }, [conversations, search]);

    const grouped = useMemo(() => groupByDate(filtered), [filtered]);

    const renderGroup = (label, items) => {
        if (items.length === 0) return null;
        return (
            <div key={label}>
                <div className="asst-conv-group-label">{label}</div>
                {items.map((c) => (
                    <ConversationItem
                        key={c.id}
                        conversation={c}
                        isActive={c.id === activeId}
                        onSelect={onSelect}
                        onDelete={onDelete}
                        onRename={onRename}
                    />
                ))}
            </div>
        );
    };

    return (
        <aside className="asst-sidebar">
            <div className="asst-sidebar-header">
                <button className="asst-new-chat-btn" onClick={onNewChat}>
                    <Plus size={16} />
                    <span>New Chat</span>
                </button>

                <div className="asst-search-wrapper">
                    <Search size={14} className="asst-search-icon" />
                    <input
                        type="text"
                        className="asst-search-input"
                        placeholder="Search conversations..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
            </div>

            <div className="asst-conv-list">
                {filtered.length === 0 ? (
                    <div className="asst-conv-empty">
                        {search ? 'No matches found' : 'No conversations yet'}
                    </div>
                ) : (
                    <>
                        {renderGroup('Today', grouped.today)}
                        {renderGroup('Yesterday', grouped.yesterday)}
                        {renderGroup('This Week', grouped.thisWeek)}
                        {renderGroup('Older', grouped.older)}
                    </>
                )}
            </div>
        </aside>
    );
};

export default ConversationSidebar;