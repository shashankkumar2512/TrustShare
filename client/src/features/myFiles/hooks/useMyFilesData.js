import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { filesAPI, foldersAPI } from '../../../utils/api';
import { events, EVENTS } from '../../../utils/events';

// ── Category mapping ──────────────────────────────────────────────────
const CATEGORY_EXTENSIONS = {
  documents:     ['pdf', 'doc', 'docx', 'txt'],
  images:        ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'],
  spreadsheets:  ['xlsx', 'xls', 'csv'],
  presentations: ['pptx', 'ppt'],
  media:         ['mp3', 'mp4', 'wav'],
  archives:      ['zip', 'rar', '7z'],
  data:          ['json', 'xml'],
};

const CATEGORY_LABELS = {
  documents:     'Documents',
  images:        'Images',
  spreadsheets:  'Spreadsheets',
  presentations: 'Presentations',
  media:         'Media',
  archives:      'Archives',
  data:          'Data',
};

const CATEGORY_ORDER = [
  'documents', 'images', 'spreadsheets', 'presentations', 'media', 'archives', 'data',
];

const getExtension = (file) => {
  const name = file?.name || file?.original_name || '';
  const parts = name.split('.');
  return parts.length > 1 ? parts.pop().toLowerCase() : '';
};

const getFileCategory = (file) => {
  const ext = getExtension(file);
  if (!ext) return 'other';
  for (const [category, extensions] of Object.entries(CATEGORY_EXTENSIONS)) {
    if (extensions.includes(ext)) return category;
  }
  return 'other';
};

// ── Sort options ──────────────────────────────────────────────────
const SORT_OPTIONS = [
  { id: 'date-desc', label: 'Newest first', field: 'date', direction: 'desc' },
  { id: 'date-asc',  label: 'Oldest first', field: 'date', direction: 'asc' },
  { id: 'name-asc',  label: 'Name (A → Z)', field: 'name', direction: 'asc' },
  { id: 'name-desc', label: 'Name (Z → A)', field: 'name', direction: 'desc' },
  { id: 'size-desc', label: 'Largest first', field: 'size', direction: 'desc' },
  { id: 'size-asc',  label: 'Smallest first', field: 'size', direction: 'asc' },
  { id: 'type-asc',  label: 'Type', field: 'type', direction: 'asc' },
];

const applySortToFiles = (files, sortId) => {
  const sort = SORT_OPTIONS.find((s) => s.id === sortId) || SORT_OPTIONS[0];
  const sorted = [...files];

  sorted.sort((a, b) => {
    let valA, valB;
    switch (sort.field) {
      case 'name':
        valA = (a.name || a.original_name || '').toLowerCase();
        valB = (b.name || b.original_name || '').toLowerCase();
        return sort.direction === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
      case 'size':
        valA = a.size || 0;
        valB = b.size || 0;
        return sort.direction === 'asc' ? valA - valB : valB - valA;
      case 'type':
        valA = getExtension(a);
        valB = getExtension(b);
        return valA.localeCompare(valB);
      case 'date':
      default:
        valA = new Date(a.created_at || a.last_modified || 0).getTime();
        valB = new Date(b.created_at || b.last_modified || 0).getTime();
        return sort.direction === 'asc' ? valA - valB : valB - valA;
    }
  });

  return sorted;
};

export function useMyFilesData() {
  const [files, setFiles] = useState([]);
  const [folders, setFolders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // ── Sort + View state (persisted) ─────────────────────────────────
  const [sortBy, setSortByState] = useState(() => {
    try {
      return sessionStorage.getItem('my_files_sort') || 'date-desc';
    } catch { return 'date-desc'; }
  });
  const [viewMode, setViewModeState] = useState(() => {
    try {
      return sessionStorage.getItem('my_files_view') || 'grid';
    } catch { return 'grid'; }
  });

  const setSortBy = useCallback((value) => {
    setSortByState(value);
    try { sessionStorage.setItem('my_files_sort', value); } catch {}
  }, []);
  const setViewMode = useCallback((value) => {
    setViewModeState(value);
    try { sessionStorage.setItem('my_files_view', value); } catch {}
  }, []);

  // ── Multi-select state ────────────────────────────────────────────
  const [selectedIds, setSelectedIds] = useState(new Set());
  const clearSelection = useCallback(() => setSelectedIds(new Set()), []);
  const toggleSelection = useCallback((id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const [folderPath, setFolderPath] = useState(() => {
    try {
      const saved = sessionStorage.getItem('my_files_folder_path');
      return saved ? JSON.parse(saved) : [];
    } catch { return []; }
  });
  const activeFolder = folderPath[folderPath.length - 1];

  // ── Upload state for premium modal ─────────────────────────────
  const [uploadQueue, setUploadQueue] = useState([]);
  const [uploadStats, setUploadStats] = useState({
    startTime: 0,
    totalSize: 0,
    uploadedSize: 0,
    speed: 0,
    eta: 0,
    isComplete: false,
    hasErrors: false,
    isCancellable: false,
  });
  const cancelRequestedRef = useRef(false);

  const resetUploadState = useCallback(() => {
    setUploadQueue([]);
    setUploadStats({
      startTime: 0,
      totalSize: 0,
      uploadedSize: 0,
      speed: 0,
      eta: 0,
      isComplete: false,
      hasErrors: false,
      isCancellable: false,
    });
    cancelRequestedRef.current = false;
  }, []);

  const cancelUpload = useCallback(() => {
    cancelRequestedRef.current = true;
    setUploadStats((prev) => ({ ...prev, isCancellable: false }));
  }, []);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [filesRes, foldersRes] = await Promise.allSettled([
        filesAPI.list(activeFolder?.id),
        foldersAPI.list(activeFolder?.id),
      ]);
      if (filesRes.status === 'fulfilled') {
        const rawFiles = filesRes.value?.data?.files || filesRes.value?.data || [];
        setFiles(Array.isArray(rawFiles) ? rawFiles : []);
      } else setFiles([]);
      if (foldersRes.status === 'fulfilled') {
        const rawFolders = foldersRes.value?.data || [];
        setFolders(Array.isArray(rawFolders) ? rawFolders : []);
      } else setFolders([]);
    } catch (err) {
      setError(err?.message || 'Failed to load files');
    } finally {
      setIsLoading(false);
    }
  }, [activeFolder?.id]);

  useEffect(() => { loadData(); }, [loadData]);

  useEffect(() => {
    clearSelection();
  }, [activeFolder?.id, selectedCategory, searchQuery, clearSelection]);

  useEffect(() => {
    window.dispatchEvent(new CustomEvent('my-files-path-changed', {
      detail: folderPath.map((f) => ({ id: f.id, name: f.name })),
    }));
    if (folderPath.length > 0) {
      try {
        sessionStorage.setItem('my_files_folder_path',
          JSON.stringify(folderPath.map((f) => ({ id: f.id, name: f.name }))));
      } catch {}
    } else {
      try { sessionStorage.removeItem('my_files_folder_path'); } catch {}
    }
  }, [folderPath]);

  useEffect(() => {
    const returnToRoot = () => {
      setFolderPath([]);
      setSelectedCategory('all');
      setSearchQuery('');
      clearSelection();
    };
    return events.on(EVENTS.MY_FILES_ROOT, returnToRoot);
  }, [clearSelection]);

  const filterChips = useMemo(() => {
    const presentCategories = new Set();
    files.forEach((file) => { presentCategories.add(getFileCategory(file)); });
    const chips = [{ id: 'all', label: 'All' }];
    CATEGORY_ORDER.forEach((catId) => {
      if (presentCategories.has(catId)) {
        chips.push({ id: catId, label: CATEGORY_LABELS[catId] });
      }
    });
    if (presentCategories.has('other')) {
      chips.push({ id: 'other', label: 'Other' });
    }
    return chips;
  }, [files]);

  const filteredFiles = useMemo(() => {
    const filtered = files.filter((file) => {
      const fileCategory = getFileCategory(file);
      const matchesCategory = selectedCategory === 'all' || fileCategory === selectedCategory;
      const fileName = (file.name || file.original_name || '').toLowerCase();
      const matchesSearch = !searchQuery || fileName.includes(searchQuery.toLowerCase());
      return matchesCategory && matchesSearch;
    });
    return applySortToFiles(filtered, sortBy);
  }, [files, selectedCategory, searchQuery, sortBy]);

  const toggleSelectAll = useCallback(() => {
    setSelectedIds((prev) => {
      if (prev.size === filteredFiles.length && filteredFiles.length > 0) {
        return new Set();
      }
      return new Set(filteredFiles.map((f) => f.id));
    });
  }, [filteredFiles]);

  const allSelected =
    filteredFiles.length > 0 && selectedIds.size === filteredFiles.length;

  const uploadFiles = async (fileList) => {
    if (!fileList || fileList.length === 0) return;

    cancelRequestedRef.current = false;
    const startTime = Date.now();
    const initialQueue = Array.from(fileList).map((f, i) => ({
      id: `upload-${startTime}-${i}`,
      file: f,
      name: f.name,
      size: f.size,
      progress: 0,
      status: 'queued',
      error: null,
    }));

    const totalSize = initialQueue.reduce((sum, f) => sum + (f.size || 0), 0);

    setUploadQueue(initialQueue);
    setUploadStats({
      startTime,
      totalSize,
      uploadedSize: 0,
      speed: 0,
      eta: 0,
      isComplete: false,
      hasErrors: false,
      isCancellable: initialQueue.length > 1,
    });
    setUploading(true);
    setUploadProgress(0);

    let completedSize = 0;
    let hasAnyError = false;
    const errors = [];

    for (let i = 0; i < initialQueue.length; i++) {
      const queueItem = initialQueue[i];

      if (cancelRequestedRef.current) {
        setUploadQueue((prev) =>
          prev.map((q) =>
            q.status === 'queued' ? { ...q, status: 'cancelled' } : q
          )
        );
        break;
      }

      setUploadQueue((prev) =>
        prev.map((q) =>
          q.id === queueItem.id ? { ...q, status: 'uploading', progress: 0 } : q
        )
      );

      let currentFileBytes = 0;

      try {
        const formData = new FormData();
        formData.append('file', queueItem.file);

        await filesAPI.upload(
          formData,
          (pct) => {
            setUploadQueue((prev) =>
              prev.map((q) => (q.id === queueItem.id ? { ...q, progress: pct } : q))
            );
            currentFileBytes = (queueItem.size * pct) / 100;
            const totalUploaded = completedSize + currentFileBytes;
            const elapsed = (Date.now() - startTime) / 1000;
            const speed = elapsed > 0 ? totalUploaded / elapsed : 0;
            const remaining = totalSize - totalUploaded;
            const eta = speed > 0 ? remaining / speed : 0;

            setUploadStats((prev) => ({
              ...prev,
              uploadedSize: totalUploaded,
              speed,
              eta,
            }));
            setUploadProgress(
              Math.round((totalUploaded / totalSize) * 100)
            );
          },
          activeFolder?.id
        );

        completedSize += queueItem.size || 0;
        setUploadQueue((prev) =>
          prev.map((q) =>
            q.id === queueItem.id ? { ...q, status: 'completed', progress: 100 } : q
          )
        );
      } catch (err) {
        hasAnyError = true;
        const detail = err?.response?.data?.detail;
        const message = typeof detail === 'string'
          ? detail
          : `Failed to upload "${queueItem.name}"`;
        errors.push(message);

        setUploadQueue((prev) =>
          prev.map((q) =>
            q.id === queueItem.id ? { ...q, status: 'failed', error: message } : q
          )
        );
      }
    }

    await loadData();
    events.emit(EVENTS.FILE_UPLOADED);
    events.emit(EVENTS.STORAGE_CHANGED);
    events.emit(EVENTS.NOTIFICATIONS_CHANGED);

    setUploadStats((prev) => ({
      ...prev,
      isComplete: true,
      hasErrors: hasAnyError,
      isCancellable: false,
      speed: 0,
      eta: 0,
    }));
    setUploading(false);
    setUploadProgress(0);

    if (errors.length > 0) {
      throw new Error(errors.join('\n'));
    }
  };

  const createFolder = async (folderName) => {
    if (!folderName || !folderName.trim()) return;
    try {
      await foldersAPI.create(folderName.trim(), activeFolder?.id);
      await loadData();
      events.emit(EVENTS.NOTIFICATIONS_CHANGED);
    } catch (err) { console.error('Create folder failed:', err); throw err; }
  };

  const renameFolder = async (folderId, newName) => {
    if (!folderId || !newName || !newName.trim()) return;
    try {
      await foldersAPI.rename(folderId, newName.trim());
      await loadData();
    } catch (err) { console.error('Rename folder failed:', err); throw err; }
  };

  const deleteFile = async (id) => {
    try {
      await filesAPI.delete(id);
      setFiles((prev) => prev.filter((f) => f.id !== id));
      setSelectedIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
      events.emit(EVENTS.FILE_DELETED, id);
      events.emit(EVENTS.STORAGE_CHANGED);
    } catch (err) { console.error('Delete file failed:', err); throw err; }
  };

  const bulkDeleteFiles = async (ids) => {
    const idList = Array.from(ids);
    if (idList.length === 0) return { success: 0, failed: 0 };

    let success = 0;
    let failed = 0;
    const results = await Promise.allSettled(
      idList.map((id) => filesAPI.delete(id))
    );
    results.forEach((r, i) => {
      if (r.status === 'fulfilled') success++;
      else { failed++; console.error(`Failed to delete file ${idList[i]}:`, r.reason); }
    });

    setFiles((prev) => prev.filter((f) => !ids.has(f.id)));
    clearSelection();
    events.emit(EVENTS.STORAGE_CHANGED);
    if (success > 0) events.emit(EVENTS.FILE_DELETED);
    return { success, failed };
  };

  const deleteFolder = async (id) => {
    try {
      await foldersAPI.delete(id, true);
      setFolders((prev) => prev.filter((f) => f.id !== id));
      events.emit(EVENTS.STORAGE_CHANGED);
    } catch (err) { console.error('Delete folder failed:', err); throw err; }
  };

  const downloadFile = async (file) => {
    const fileName = file.name || file.original_name || 'download';
    const response = await filesAPI.download(file.id);
    const mimeType =
      response.headers?.['content-type'] || file.mimetype || 'application/octet-stream';
    const url = window.URL.createObjectURL(new Blob([response.data], { type: mimeType }));
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => window.URL.revokeObjectURL(url), 1000);
    events.emit(EVENTS.NOTIFICATIONS_CHANGED);
  };

  //  Multi-File moving logic 
  const moveFile = async (fileId, folderId) => {
    const ids = Array.isArray(fileId) ? fileId : [fileId];
    const response = await Promise.all(
      ids.map((id) => filesAPI.move(id, folderId))
    );
    await loadData();
    clearSelection();
    return response;
  };

  const openFolder = (folder) => {
    setFolderPath((current) => [...current, folder]);
    setSelectedCategory('all');
    setSearchQuery('');
  };

  const goToFolder = (index) => {
    setFolderPath((current) => current.slice(0, index + 1));
    setSelectedCategory('all');
    setSearchQuery('');
  };

  return {
    files,
    folders,
    folderCards: folders.map((f, i) => ({
      id: f.id || `folder-${i}`,
      title: f.name || 'Untitled Folder',
      subtitle: `${f.item_count ?? 0} item${f.item_count === 1 ? '' : 's'}`,
    })),
    filterChips,
    selectedCategory,
    searchQuery,
    filteredFiles,
    isLoading,
    error,
    uploading,
    uploadProgress,
    folderPath,

    sortBy,
    setSortBy,
    sortOptions: SORT_OPTIONS,
    viewMode,
    setViewMode,

    selectedIds,
    toggleSelection,
    clearSelection,
    toggleSelectAll,
    allSelected,

    uploadQueue,
    uploadStats,
    cancelUpload,
    resetUploadState,

    setSelectedCategory,
    setSearchQuery,
    refetch: loadData,
    uploadFiles,
    createFolder,
    renameFolder,
    deleteFile,
    bulkDeleteFiles,
    deleteFolder,
    downloadFile,
    moveFile,
    openFolder,
    goToFolder,
    goToRoot: () => {
      setFolderPath([]);
      setSelectedCategory('all');
      setSearchQuery('');
      clearSelection();
    },
  };
}