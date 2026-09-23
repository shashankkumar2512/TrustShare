import { useEffect, useRef, useState } from 'react';
import { FolderPlus, Pencil, X, Loader2 } from 'lucide-react';

export default function FolderModal({
  isOpen,
  onClose,
  onSubmit,
  mode = 'create', // 'create' | 'rename'
  initialName = '',
}) {
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef(null);

  const isRename = mode === 'rename';
  const Icon = isRename ? Pencil : FolderPlus;
  const title = isRename ? 'Rename folder' : 'New folder';
  const submitText = isRename ? 'Rename' : 'Create';
  const placeholder = isRename ? 'Enter new folder name' : 'e.g. Project Documents';

  useEffect(() => {
    if (!isOpen) return;
    setName(initialName || '');
    setError('');
    setTimeout(() => inputRef.current?.focus(), 50);
  }, [isOpen, initialName]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e) => {
      if (e.key === 'Escape' && !loading) onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, loading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      setError('Folder name is required');
      return;
    }
    if (isRename && trimmed === initialName) {
      onClose();
      return;
    }
    setLoading(true);
    setError('');
    try {
      await onSubmit(trimmed);
      onClose();
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Something went wrong');
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
      <div className="my-files-modal my-files-modal--primary" role="dialog" aria-modal="true">
        <button
          type="button"
          className="my-files-modal-close"
          onClick={() => !loading && onClose()}
          aria-label="Close"
          disabled={loading}
        >
          <X size={16} strokeWidth={2.4} />
        </button>

        <div className="my-files-modal-icon my-files-modal-icon--primary">
          <Icon size={26} strokeWidth={2} />
        </div>

        <h2 className="my-files-modal-title">{title}</h2>
        <p className="my-files-modal-message">
          {isRename ? 'Choose a new name for this folder.' : 'Give your folder a memorable name.'}
        </p>

        <form onSubmit={handleSubmit} className="my-files-modal-form">
          <input
            ref={inputRef}
            type="text"
            value={name}
            onChange={(e) => { setName(e.target.value); if (error) setError(''); }}
            placeholder={placeholder}
            className="my-files-modal-input"
            maxLength={100}
            disabled={loading}
          />
          {error && <p className="my-files-modal-error">{error}</p>}

          <div className="my-files-modal-actions">
            <button
              type="button"
              className="my-files-btn my-files-btn--secondary"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="my-files-btn my-files-btn--primary"
              disabled={loading || !name.trim()}
            >
              {loading ? (
                <>
                  <Loader2 size={14} className="my-files-spin" strokeWidth={2.2} />
                  Please wait…
                </>
              ) : (
                submitText
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}