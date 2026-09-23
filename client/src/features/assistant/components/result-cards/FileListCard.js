import React from 'react';
import { motion } from 'framer-motion';
import { FileText, Image, Video, Music, FileArchive, File as FileIcon, Lock } from 'lucide-react';

const iconForType = (type) => {
    switch (type) {
        case 'pdf':
        case 'document':
            return <FileText size={18} />;
        case 'image':
            return <Image size={18} />;
        case 'video':
            return <Video size={18} />;
        case 'audio':
            return <Music size={18} />;
        case 'archive':
            return <FileArchive size={18} />;
        default:
            return <FileIcon size={18} />;
    }
};

const FileListCard = ({ result }) => {
    const files = result?.files || [];
    const total = result?.total_matched || files.length;

    if (files.length === 0) {
        return (
            <div className="asst-card">
                <div className="asst-card-empty">
                    <FileIcon size={32} className="asst-card-empty-icon" />
                    <div className="asst-card-empty-title">No files found</div>
                    <div className="asst-card-empty-subtitle">Try adjusting your filters</div>
                </div>
            </div>
        );
    }

    return (
        <div className="asst-card">
            <div className="asst-card-header">
                <div className="asst-card-header-left">
                    <div className="asst-card-title">
                        {result?.query ? `Search: "${result.query}"` : 'Files Found'}
                    </div>
                </div>
                <div className="asst-card-meta">
                    Showing {files.length} of {total}
                </div>
            </div>

            <div className="asst-card-body-flush">
                {files.map((f, idx) => (
                    <motion.div
                        key={f.id || idx}
                        className="asst-file-row"
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.03 }}
                    >
                        <div className={`asst-file-icon ${f.type || 'other'}`}>
                            {iconForType(f.type)}
                        </div>
                        <div className="asst-file-info">
                            <div className="asst-file-name">
                                {f.name}
                                {f.encrypted && <Lock size={12} className="asst-file-lock-icon" />}
                            </div>
                            <div className="asst-file-meta">
                                {f.size} · {f.created}
                                {f.download_count > 0 && ` · ${f.download_count} downloads`}
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    );
};

export default FileListCard;