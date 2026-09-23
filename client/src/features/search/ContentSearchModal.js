import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RiSearch2Line, RiCloseLine, RiFileTextLine, RiFileSearchLine } from "react-icons/ri";
import { searchAPI } from "../../utils/api";
import "./ContentSearchModal.css";

export default function ContentSearchModal({ isOpen, onClose }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [totalResults, setTotalResults] = useState(0);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setTotalResults(0);
      setLoading(false);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setLoading(true);
        const res = await searchAPI.searchContent(query);
        setResults(res.data.results || []);
        setTotalResults(res.data.total_results || 0);
      } catch (err) {
        console.error("Content search failed:", err);
        setResults([]);
        setTotalResults(0);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="content-search-overlay" onClick={onClose}>
        <motion.div
          className="content-search-modal"
          onClick={(e) => e.stopPropagation()}
          initial={{ opacity: 0, scale: 0.95, y: -20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -20 }}
          transition={{ duration: 0.2 }}
        >
          <div className="content-search-header">
            <div className="content-search-badge">
              <RiFileSearchLine className="search-badge-icon" size={16} /> Deep Content Search
            </div>
            <button className="content-search-close" onClick={onClose} aria-label="Close search modal">
              <RiCloseLine size={20} />
            </button>
          </div>

          <div className="content-search-input-wrapper">
            <RiSearch2Line className="search-modal-icon" />
            <input
              type="text"
              placeholder="Search inside file contents (PDF, DOCX, TXT, PPTX)..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              autoFocus
            />
            {query && (
              <button className="clear-search-btn" onClick={() => setQuery("")}>
                Clear
              </button>
            )}
          </div>

          <div className="content-search-body">
            {loading && (
              <div className="content-search-loading">
                <div className="search-spinner" />
                <span>Scanning document contents...</span>
              </div>
            )}

            {!loading && query && results.length === 0 && (
              <div className="content-search-empty">
                <RiFileTextLine size={36} />
                <p className="empty-title">No content matches found</p>
                <p className="empty-desc">No uploaded documents contained the phrase "{query}".</p>
              </div>
            )}

            {!loading && results.length > 0 && (
              <div className="content-search-results">
                <div className="results-count-bar">
                  Found <strong>{totalResults}</strong> matching {totalResults === 1 ? "document" : "documents"}
                </div>
                {results.map((res) => (
                  <div key={res.id} className="content-result-card">
                    <div className="card-header">
                      <RiFileTextLine className="file-icon" />
                      <span className="file-title">{res.original_name}</span>
                      <span className="match-badge">{res.match_count} {res.match_count === 1 ? "match" : "matches"}</span>
                    </div>
                    <div
                      className="card-snippet"
                      dangerouslySetInnerHTML={{ __html: res.snippet }}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}