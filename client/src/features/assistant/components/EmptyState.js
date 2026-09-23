import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';
import SuggestedQueries from './SuggestedQueries';

const EmptyState = ({ botName = 'TrustShare Assistant', onPickSuggestion, compact = false }) => {
    return (
        <div className="asst-empty">
            <motion.div
                className="asst-empty-icon"
                initial={{ scale: 0.6, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.5, ease: [0.32, 0.72, 0, 1] }}
            >
                <Sparkles size={36} />
            </motion.div>
            <motion.h2
                className="asst-empty-title"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1, duration: 0.4 }}
            >
                Hi! I'm {botName} ✨
            </motion.h2>
            <motion.p
                className="asst-empty-subtitle"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15, duration: 0.4 }}
            >
                I can help you find files, check your storage, review shares, and answer
                questions about your account. Try asking me anything!
            </motion.p>
            <motion.div
                style={{ width: '100%', maxWidth: 720 }}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2, duration: 0.4 }}
            >
                <SuggestedQueries onPick={onPickSuggestion} compact={compact} />
            </motion.div>
        </div>
    );
};

export default EmptyState;