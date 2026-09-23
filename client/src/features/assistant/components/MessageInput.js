import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';

const MessageInput = ({ onSend, disabled = false, maxLength = 2000, placeholder = 'Ask me anything...' }) => {
    const [value, setValue] = useState('');
    const textareaRef = useRef(null);

    useEffect(() => {
        const ta = textareaRef.current;
        if (ta) {
            ta.style.height = 'auto';
            ta.style.height = `${Math.min(ta.scrollHeight, 180)}px`;
        }
    }, [value]);

    const handleSubmit = (e) => {
        e?.preventDefault();
        const trimmed = value.trim();
        if (!trimmed || disabled) return;
        onSend(trimmed);
        setValue('');

        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    const canSend = value.trim().length > 0 && !disabled;
    const charsLeft = maxLength - value.length;

    return (
        <div className="asst-input-area">
            <form onSubmit={handleSubmit} className="asst-input-wrapper">
                <textarea
                    ref={textareaRef}
                    className="asst-input-textarea"
                    value={value}
                    onChange={(e) => setValue(e.target.value.slice(0, maxLength))}
                    onKeyDown={handleKeyDown}
                    placeholder={disabled ? 'Waiting for response...' : placeholder}
                    rows={1}
                    disabled={disabled}
                />
                <button
                    type="submit"
                    className="asst-send-btn"
                    disabled={!canSend}
                    aria-label="Send message"
                >
                    {disabled ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
                </button>
            </form>
            <div className="asst-input-hint">
                Press <kbd>Enter</kbd> to send · <kbd>Shift + Enter</kbd> for new line
                {charsLeft < 200 && ` · ${charsLeft} characters left`}
            </div>
        </div>
    );
};

export default MessageInput;