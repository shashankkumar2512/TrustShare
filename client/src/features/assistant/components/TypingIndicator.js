import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';

const TypingIndicator = () => (
    <motion.div
        className="asst-typing"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
    >
        <div className="asst-msg-avatar assistant">
            <Sparkles size={16} />
        </div>
        <div className="asst-typing-bubble">
            <span className="asst-typing-dot" />
            <span className="asst-typing-dot" />
            <span className="asst-typing-dot" />
        </div>
    </motion.div>
);

export default TypingIndicator;