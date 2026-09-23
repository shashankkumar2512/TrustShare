import React, { useEffect, useRef } from 'react';
import { AnimatePresence } from 'framer-motion';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';

const MessageList = ({
    messages = [],
    sending = false,
    onRegenerate,
    canRegenerate = false,
    enableMarkdown = true,
    showTokenUsage = false,
}) => {
    const bottomRef = useRef(null);

    useEffect(() => {
        if (bottomRef.current) {
            bottomRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
    }, [messages.length, sending]);

    const lastAssistantIndex = [...messages]
        .reverse()
        .findIndex((m) => m.role === 'assistant' && !m.isError);
    const lastAssistantIdx = lastAssistantIndex === -1
        ? -1
        : messages.length - 1 - lastAssistantIndex;

    return (
        <div className="asst-messages">
            <div className="asst-messages-inner">
                <AnimatePresence initial={false}>
                    {messages.map((msg, idx) => (
                        <MessageBubble
                            key={msg.id}
                            message={msg}
                            onRegenerate={onRegenerate}
                            canRegenerate={canRegenerate}
                            enableMarkdown={enableMarkdown}
                            showTokenUsage={showTokenUsage}
                            isLast={idx === lastAssistantIdx}
                        />
                    ))}
                    {sending && <TypingIndicator key="typing" />}
                </AnimatePresence>
                <div ref={bottomRef} />
            </div>
        </div>
    );
};

export default MessageList;