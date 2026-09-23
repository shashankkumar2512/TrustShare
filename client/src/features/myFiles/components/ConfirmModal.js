import { useEffect, useState } from 'react';
import { AlertTriangle, X, Loader2 } from 'lucide-react';

export default function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title = 'Are you sure?',
  message = 'This action cannot be undone.',
  confirmText = 'Delete',
  cancelText = 'Cancel',
  variant = 'danger', // 'danger' | 'primary'
  icon: Icon = AlertTriangle,
}) {
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e) => {
      if (e.key === 'Escape' && !loading) onClose();
      if (e.key === 'Enter' && !loading) handleConfirm();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, loading]);

  const handleConfirm = async () => {
    setLoading(true);
    try {
      await onConfirm();
      onClose();
    } catch {
      // Error is handled by caller — just stop loading
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="my-files-modal-overlay"
      onMouseDown={(e) => e.target === e.currentTarget && !loading && onClose()}
    >
      <div className={`my-files-modal my-files-modal--${variant}`} role="dialog" aria-modal="true">
        <button
          type="button"
          className="my-files-modal-close"
          onClick={() => !loading && onClose()}
          aria-label="Close"
          disabled={loading}
        >
          <X size={16} strokeWidth={2.4} />
        </button>

        <div className={`my-files-modal-icon my-files-modal-icon--${variant}`}>
          <Icon size={26} strokeWidth={2} />
        </div>

        <h2 className="my-files-modal-title">{title}</h2>
        <p className="my-files-modal-message">{message}</p>

        <div className="my-files-modal-actions">
          <button
            type="button"
            className="my-files-btn my-files-btn--secondary"
            onClick={onClose}
            disabled={loading}
          >
            {cancelText}
          </button>
          <button
            type="button"
            className={`my-files-btn my-files-btn--${variant}`}
            onClick={handleConfirm}
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 size={14} className="my-files-spin" strokeWidth={2.2} />
                Please wait…
              </>
            ) : (
              confirmText
            )}
          </button>
        </div>
      </div>
    </div>
  );
}