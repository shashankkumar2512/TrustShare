// client/src/layout/KeyboardShortcuts.js
/**
 * Keyboard shortcuts guide — press "?" to open.
 */

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { X, Keyboard } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import "./KeyboardShortcuts.css";

const SHORTCUT_GROUPS = [
  {
    title: "Navigation",
    shortcuts: [
      { keys: ["Ctrl", "K"], label: "Open search" },
      { keys: ["Ctrl", "/"], label: "Open AI Assistant" },
      { keys: ["Esc"], label: "Close search / dropdowns" },
      { keys: ["?"], label: "Show keyboard shortcuts" },
    ],
  },
  {
    title: "Search",
    shortcuts: [
      { keys: ["↑", "↓"], label: "Navigate results" },
      { keys: ["↵"], label: "Select result" },
      { keys: ["Esc"], label: "Close search" },
    ],
  },
  {
    title: "General",
    shortcuts: [
      { keys: ["Ctrl", "Shift", "D"], label: "Toggle dark mode" },
    ],
  },
];

export default function KeyboardShortcuts() {
  const [open, setOpen] = useState(false);
  const { toggleTheme } = useTheme();

  useEffect(() => {
    const handleKey = (e) => {
      const isTyping = ["INPUT", "TEXTAREA", "SELECT"].includes(
        document.activeElement?.tagName
      );

      if (e.key === "?" && !isTyping) {
        e.preventDefault();
        setOpen((prev) => !prev);
      }

      if (e.key === "Escape" && open) {
        setOpen(false);
      }

      if (e.ctrlKey && e.shiftKey && e.key === "D") {
        e.preventDefault();
        toggleTheme();
      }

      // Open AI Assistant with Ctrl+/ (or Cmd+/ on Mac)
      if ((e.ctrlKey || e.metaKey) && e.key === "/" && !isTyping) {
        e.preventDefault();
        window.dispatchEvent(new CustomEvent("assistant:open"));
      }
    };

    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open, toggleTheme]);

  return createPortal(
    <AnimatePresence>
      {open && (
        <motion.div
          className="shortcuts-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          onClick={(e) => {
            if (e.target === e.currentTarget) setOpen(false);
          }}
        >
          <motion.div
            className="shortcuts-modal"
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.92 }}
            transition={{ duration: 0.25, ease: [0.32, 0.72, 0, 1] }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="shortcuts-header">
              <div className="shortcuts-header-left">
                <Keyboard size={18} />
                <h3>Keyboard Shortcuts</h3>
              </div>
              <button
                className="shortcuts-close"
                onClick={() => setOpen(false)}
                aria-label="Close"
              >
                <X size={16} />
              </button>
            </div>

            <div className="shortcuts-body">
              {SHORTCUT_GROUPS.map((group) => (
                <div key={group.title} className="shortcuts-group">
                  <h4 className="shortcuts-group-title">{group.title}</h4>
                  {group.shortcuts.map((shortcut) => (
                    <div key={shortcut.label} className="shortcuts-row">
                      <span className="shortcuts-label">{shortcut.label}</span>
                      <div className="shortcuts-keys">
                        {shortcut.keys.map((key, i) => (
                          <React.Fragment key={key}>
                            {i > 0 && (
                              <span className="shortcuts-plus">+</span>
                            )}
                            <kbd className="shortcuts-kbd">{key}</kbd>
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>

            <div className="shortcuts-footer">
              <span>
                Press <kbd className="shortcuts-kbd">?</kbd> to toggle
              </span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body
  );
}