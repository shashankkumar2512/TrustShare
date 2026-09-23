import React from 'react';
import { motion } from 'framer-motion';
import { HardDrive, Crown } from 'lucide-react';

const StorageCard = ({ result }) => {
    const percent = result?.usage_percent ?? 0;
    const isHigh = percent > 75;
    const isCritical = percent > 90;

    const fillClass = isCritical ? 'critical' : isHigh ? 'high' : 'normal';

    return (
        <div className="asst-card">
            <div className="asst-card-body">
                {/* Header */}
                <div className="asst-storage-header">
                    <div className="asst-card-icon-box lg">
                        <HardDrive size={22} />
                    </div>
                    <div style={{ flex: 1 }}>
                        <div className="asst-card-title" style={{ fontSize: 15 }}>
                            Storage Usage
                        </div>
                        <div className="asst-storage-plan">
                            <Crown size={11} />
                            <span>{result?.plan || 'free'} plan</span>
                        </div>
                    </div>
                </div>

                {/* Big number */}
                <div className="asst-storage-big">
                    {result?.used}
                    <span className="asst-storage-big-quota">of {result?.quota}</span>
                </div>

                {/* Progress bar */}
                <div className="asst-storage-bar-track">
                    <motion.div
                        className={`asst-storage-bar-fill ${fillClass}`}
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min(percent, 100)}%` }}
                        transition={{ duration: 0.8, ease: [0.32, 0.72, 0, 1] }}
                    />
                </div>

                {/* Stats */}
                <div className="asst-storage-stats">
                    <div>
                        <span className="asst-storage-stat-label">Used: </span>
                        <span className="asst-storage-stat-value">{percent}%</span>
                    </div>
                    <div>
                        <span className="asst-storage-stat-label">Available: </span>
                        <span className="asst-storage-stat-value">{result?.remaining}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default StorageCard;