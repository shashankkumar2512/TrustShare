import React, { useCallback, useState } from 'react';
import { CheckCircle2, XCircle } from 'lucide-react';
import SharedWithMeError from './components/SharedWithMeError';
import SharedWithMeLoading from './components/SharedWithMeLoading';
import SharedFilesView from './components/SharedFilesView';
import { useSharedFiles } from './hooks/useSharedFiles';
import { downloadSharedFile, viewSharedFile } from './services/sharedWithMeService';
import './sharedWithMe.css';

export default function SharedWithMeFeature() {
  const { data, error, isLoading, refetch } = useSharedFiles();
  const [toast, setToast] = useState(null);

  const showToast = useCallback((text, isError = false) => {
    setToast({ text, isError });
    setTimeout(() => setToast(null), 3500);
  }, []);

  const handleDownload = useCallback(async (file) => {
    const fileName = file?.name || 'document';
    showToast(`🔒 Decrypting "${fileName}"…`);
    try {
      await downloadSharedFile(file);
      showToast(`✅ "${fileName}" downloaded`);
    } catch (err) {
      showToast(err?.response?.data?.detail || 'File download failed.', true);
      throw err;
    }
  }, [showToast]);

  const handleView = useCallback(async (file) => {
    const fileName = file?.name || 'document';
    showToast(`🔒 Opening "${fileName}"…`);
    try {
      await viewSharedFile(file);
      showToast(`✅ "${fileName}" opened in secure viewer`);
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to open file.', true);
      throw err;
    }
  }, [showToast]);

  if (isLoading) return <SharedWithMeLoading />;
  if (error) return <SharedWithMeError onRetry={refetch} />;

  const normalizedData = {
    ...data,
    files: (data?.files || []).map((f) => ({
      ...f,
      id: f.file_id,
      original_name: f.name,
    })),
  };

  return (
    <>
      {toast && (
        <div className={`my-files-toast ${toast.isError ? 'is-error' : 'is-success'}`}>
          {toast.isError ? <XCircle size={16} /> : <CheckCircle2 size={16} />}
          <span>{toast.text}</span>
        </div>
      )}

      <SharedFilesView
        data={normalizedData}
        onDownload={handleDownload}
        onView={handleView}
      />
    </>
  );
}