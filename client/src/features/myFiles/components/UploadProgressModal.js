import { useMemo } from 'react';
import {
  CheckCircle2,
  XCircle,
  Loader2,
  X,
  Upload,
  FileText,
  FileImage,
  FileVideo,
  FileAudio,
  FileArchive,
  FileSpreadsheet,
  File as FileIcon,
  Ban,
} from 'lucide-react';

// ── File icon resolver ─────────────────────────────────────────────────
const getFileIcon = (name = '') => {
  const ext = name.split('.').pop()?.toLowerCase() || '';
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'].includes(ext)) return FileImage;
  if (['mp4', 'webm', 'avi', 'mov', 'mkv'].includes(ext)) return FileVideo;
  if (['mp3', 'wav', 'ogg', 'flac'].includes(ext)) return FileAudio;
  if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return FileArchive;
  if (['xlsx', 'xls', 'csv'].includes(ext)) return FileSpreadsheet;
  if (['pdf', 'doc', 'docx', 'txt', 'md', 'pptx', 'ppt'].includes(ext)) return FileText;
  return FileIcon;
};

const formatSize = (bytes) => {
  if (!bytes || isNaN(bytes)) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1073741824) return `${(bytes / 1048576).toFixed(1)} MB`;
  return `${(bytes / 1073741824).toFixed(2)} GB`;
};

const formatSpeed = (bytesPerSec) => {
  if (!bytesPerSec || bytesPerSec < 1) return '—';
  if (bytesPerSec < 1024) return `${Math.round(bytesPerSec)} B/s`;
  if (bytesPerSec < 1048576) return `${(bytesPerSec / 1024).toFixed(1)} KB/s`;
  return `${(bytesPerSec / 1048576).toFixed(1)} MB/s`;
};

const formatEta = (seconds) => {
  if (!seconds || !isFinite(seconds) || seconds < 1) return '—';
  if (seconds < 60) return `${Math.ceil(seconds)}s remaining`;
  if (seconds < 3600) {
    const m = Math.floor(seconds / 60);
    const s = Math.ceil(seconds % 60);
    return `${m}m ${s}s remaining`;
  }
  return `${Math.floor(seconds / 3600)}h remaining`;
};

export default function UploadProgressModal({
  isOpen,
  files = [],
  overallProgress = 0,
  speed = 0,
  eta = 0,
  totalSize = 0,
  uploadedSize = 0,
  isCancellable = false,
  onCancel,
  onClose,
  isComplete = false,
  hasErrors = false,
}) {
  // Derived counts
  const { completed, failed, cancelled, queued, uploading } = useMemo(() => {
    return files.reduce(
      (acc, f) => {
        acc[f.status] = (acc[f.status] || 0) + 1;
        return acc;
      },
      { completed: 0, failed: 0, cancelled: 0, queued: 0, uploading: 0 }
    );
  }, [files]);

  if (!isOpen) return null;

  const successRate = files.length > 0 ? Math.round((completed / files.length) * 100) : 0;
  const canClose = isComplete;

  return (
    <div
      className="upload-modal-overlay"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && canClose) onClose();
      }}
    >
      <div className="upload-modal" role="dialog" aria-modal="true">
        {/* Header */}
        <div className="upload-modal-header">
          <div className="upload-modal-header-left">
            <div className={`upload-modal-icon ${isComplete && hasErrors ? 'is-warning' : isComplete ? 'is-success' : 'is-uploading'}`}>
              {isComplete ? (
                hasErrors ? <XCircle size={22} strokeWidth={2} /> : <CheckCircle2 size={22} strokeWidth={2} />
              ) : (
                <Upload size={22} strokeWidth={2} />
              )}
            </div>
            <div>
              <h2 className="upload-modal-title">
                {isComplete
                  ? hasErrors
                    ? `Upload finished with ${failed} error${failed > 1 ? 's' : ''}`
                    : `${completed} file${completed > 1 ? 's' : ''} uploaded`
                  : `Uploading ${files.length} file${files.length > 1 ? 's' : ''}…`}
              </h2>
              <p className="upload-modal-subtitle">
                {isComplete ? (
                  <>
                    {completed > 0 && <span className="upload-stat upload-stat--success">✓ {completed} succeeded</span>}
                    {failed > 0 && <span className="upload-stat upload-stat--error">✗ {failed} failed</span>}
                    {cancelled > 0 && <span className="upload-stat upload-stat--muted">⊘ {cancelled} cancelled</span>}
                  </>
                ) : (
                  <>
                    <span>{formatSize(uploadedSize)} / {formatSize(totalSize)}</span>
                    <span className="upload-stat-sep">•</span>
                    <span>{formatSpeed(speed)}</span>
                    <span className="upload-stat-sep">•</span>
                    <span>{formatEta(eta)}</span>
                  </>
                )}
              </p>
            </div>
          </div>

          {canClose && (
            <button
              type="button"
              className="upload-modal-close"
              onClick={onClose}
              aria-label="Close"
            >
              <X size={16} strokeWidth={2.4} />
            </button>
          )}
        </div>

        {/* Overall progress bar */}
        {!isComplete && (
          <div className="upload-modal-overall">
            <div className="upload-modal-progress-track">
              <div
                className="upload-modal-progress-fill"
                style={{ width: `${overallProgress}%` }}
              />
            </div>
            <div className="upload-modal-overall-meta">
              <span className="upload-modal-percent">{Math.round(overallProgress)}%</span>
              {isCancellable && queued > 0 && (
                <button
                  type="button"
                  className="upload-modal-cancel-btn"
                  onClick={onCancel}
                  title="Cancel remaining files"
                >
                  <Ban size={12} strokeWidth={2.4} />
                  Cancel {queued} queued
                </button>
              )}
            </div>
          </div>
        )}

        {/* Success rate bar when complete */}
        {isComplete && (
          <div className="upload-modal-overall">
            <div className="upload-modal-progress-track">
              <div
                className={`upload-modal-progress-fill ${hasErrors ? 'is-partial' : 'is-success'}`}
                style={{ width: `${successRate}%` }}
              />
            </div>
            <div className="upload-modal-overall-meta">
              <span className="upload-modal-percent">{successRate}% success</span>
            </div>
          </div>
        )}

        {/* File list */}
        <div className="upload-modal-list">
          {files.map((file) => {
            const Icon = getFileIcon(file.name);
            return (
              <div key={file.id} className={`upload-file-row is-${file.status}`}>
                <div className="upload-file-icon">
                  <Icon size={16} strokeWidth={2} />
                </div>

                <div className="upload-file-info">
                  <div className="upload-file-name" title={file.name}>{file.name}</div>
                  <div className="upload-file-meta">
                    <span>{formatSize(file.size)}</span>
                    {file.status === 'uploading' && (
                      <>
                        <span className="upload-stat-sep">•</span>
                        <span>{Math.round(file.progress)}%</span>
                      </>
                    )}
                    {file.status === 'failed' && file.error && (
                      <>
                        <span className="upload-stat-sep">•</span>
                        <span className="upload-error-msg">{file.error}</span>
                      </>
                    )}
                    {file.status === 'cancelled' && (
                      <>
                        <span className="upload-stat-sep">•</span>
                        <span className="upload-cancelled-msg">Cancelled</span>
                      </>
                    )}
                  </div>

                  {file.status === 'uploading' && (
                    <div className="upload-file-progress">
                      <div
                        className="upload-file-progress-fill"
                        style={{ width: `${file.progress}%` }}
                      />
                    </div>
                  )}
                </div>

                <div className="upload-file-status">
                  {file.status === 'queued' && (
                    <span className="upload-file-badge upload-file-badge--queued">Queued</span>
                  )}
                  {file.status === 'uploading' && (
                    <Loader2 size={16} className="upload-spin" strokeWidth={2.2} />
                  )}
                  {file.status === 'completed' && (
                    <CheckCircle2 size={16} className="upload-status-success" strokeWidth={2.2} />
                  )}
                  {file.status === 'failed' && (
                    <XCircle size={16} className="upload-status-error" strokeWidth={2.2} />
                  )}
                  {file.status === 'cancelled' && (
                    <Ban size={16} className="upload-status-muted" strokeWidth={2.2} />
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        {isComplete && (
          <div className="upload-modal-footer">
            <button
              type="button"
              className="my-files-btn my-files-btn--primary"
              onClick={onClose}
              style={{ width: '100%', justifyContent: 'center' }}
            >
              {hasErrors ? 'Close' : 'Done'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}