import React from 'react';
import { motion } from 'framer-motion';
import { Share2, Link, Mail, Clock, Eye, Download } from 'lucide-react';

const SharesCard = ({ result }) => {
    const directShares = result?.direct_shares || [];
    const shareLinks = result?.share_links || [];
    const totalShares = directShares.length + shareLinks.length;

    if (totalShares === 0) {
        return (
            <div className="asst-card">
                <div className="asst-card-empty">
                    <Share2 size={32} className="asst-card-empty-icon" />
                    <div className="asst-card-empty-title">No shares found</div>
                    <div className="asst-card-empty-subtitle">You haven't shared any files yet</div>
                </div>
            </div>
        );
    }

    return (
        <div className="asst-card">
            {/* Header */}
            <div className="asst-card-header">
                <div className="asst-card-header-left">
                    <div className="asst-card-icon-box">
                        <Share2 size={18} />
                    </div>
                    <div>
                        <div className="asst-card-title">Your Shares</div>
                        <div className="asst-card-subtitle">
                            {directShares.length} direct · {shareLinks.length} links
                        </div>
                    </div>
                </div>
            </div>

            {/* Direct shares */}
            {directShares.length > 0 && (
                <div>
                    <div className="asst-card-section-label">Direct Shares</div>
                    {directShares.slice(0, 5).map((s, idx) => (
                        <motion.div
                            key={idx}
                            className="asst-share-row"
                            initial={{ opacity: 0, y: 4 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.04 }}
                        >
                            <div className="asst-share-content">
                                <div className="asst-share-info">
                                    <div className="asst-share-file-name">{s.file_name}</div>
                                    <div className="asst-share-meta">
                                        <span className="asst-share-meta-item">
                                            <Mail size={10} />
                                            {s.recipient_name} ({s.recipient_email})
                                        </span>
                                    </div>
                                </div>
                                <span className={`asst-share-permission-badge ${s.permission}`}>
                                    {s.permission === 'download' ? <Download size={10} /> : <Eye size={10} />}
                                    {s.permission}
                                </span>
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}

            {/* Share links */}
            {shareLinks.length > 0 && (
                <div>
                    <div className="asst-card-section-label">Share Links</div>
                    {shareLinks.slice(0, 5).map((l, idx) => (
                        <motion.div
                            key={idx}
                            className="asst-share-row"
                            initial={{ opacity: 0, y: 4 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.04 }}
                        >
                            <div className="asst-share-content">
                                <div className="asst-share-info">
                                    <div className="asst-share-file-name">
                                        <Link size={12} style={{ color: 'var(--asst-text-muted)' }} />
                                        {l.file_name}
                                    </div>
                                    <div className="asst-share-meta">
                                        <span className="asst-share-meta-item">
                                            <Clock size={10} /> Expires: {l.expires}
                                        </span>
                                        <span>{l.access_count} accesses</span>
                                    </div>
                                </div>
                                <span className={`asst-share-active-dot ${l.is_active ? 'active' : 'inactive'}`} />
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default SharesCard;