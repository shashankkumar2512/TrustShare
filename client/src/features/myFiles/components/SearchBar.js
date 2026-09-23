import { Search, X } from 'lucide-react';

export default function SearchBar({ value, onChange, onClear }) {
  return (
    <label className="my-files-search">
      <span className="sr-only">Search files</span>
      <span className="my-files-search-icon">
        <Search size={16} strokeWidth={2} />
      </span>
      <input
        type="text"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Search files, folders, and tags"
        className="my-files-search-input"
      />
      {value && (
        <button
          type="button"
          onClick={onClear}
          aria-label="Clear file search"
          className="my-files-search-clear"
        >
          <X size={14} strokeWidth={2.4} />
        </button>
      )}
    </label>
  );
}