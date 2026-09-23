import React from 'react';
import { motion } from 'framer-motion';
import { Monitor, Smartphone, Tablet, Laptop, MapPin } from 'lucide-react';

const iconForDevice = (deviceType) => {
    switch (deviceType?.toLowerCase()) {
        case 'mobile':
        case 'phone':
            return <Smartphone size={16} />;
        case 'tablet':
            return <Tablet size={16} />;
        case 'desktop':
            return <Monitor size={16} />;
        default:
            return <Laptop size={16} />;
    }
};

const SessionsCard = ({ result }) => {
    const sessions = result?.sessions || [];

    if (sessions.length === 0) {
        return (
            <div className="asst-card">
                <div className="asst-card-empty">
                    <div className="asst-card-empty-title">No active sessions</div>
                </div>
            </div>
        );
    }

    return (
        <div className="asst-card">
            {/* Header */}
            <div className="asst-card-header">
                <div className="asst-card-header-left">
                    <div className="asst-card-title">Active Sessions</div>
                </div>
                <span className="asst-card-meta">
                    {result.total_sessions} total
                </span>
            </div>

            {/* Session rows */}
            <div className="asst-card-body-flush">
                {sessions.map((s, idx) => (
                    <motion.div
                        key={idx}
                        className="asst-session-row"
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.04 }}
                    >
                        <div className={`asst-session-icon ${s.is_current ? 'current' : ''}`}>
                            {iconForDevice(s.device_type)}
                        </div>
                        <div className="asst-session-info">
                            <div className="asst-session-browser">
                                {s.browser}
                                {s.is_current && (
                                    <span className="asst-session-current-badge">Current</span>
                                )}
                            </div>
                            <div className="asst-session-meta">
                                <span className="asst-session-meta-location">
                                    <MapPin size={10} /> {s.location} · {s.ip}
                                </span>
                                <span>· {s.last_active}</span>
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    );
};

export default SessionsCard;