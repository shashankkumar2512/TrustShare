// client/src/features/analytics/components/Header/DateRangeDropdown.js

import React, { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Check, Calendar, ArrowRight, ArrowLeft } from "lucide-react";

const NAVBAR_HEIGHT = 72;

export default function DateRangeDropdown({
  options = [],
  value = "",
  onChange,
}) {
  const [open, setOpen] = useState(false);
  const [menuPos, setMenuPos] = useState({ top: 0, left: 0, width: 0 });
  const [showCustom, setShowCustom] = useState(false);
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");
  const [activePreset, setActivePreset] = useState(null);
  const triggerRef = useRef(null);
  const menuRef = useRef(null);

  const updatePosition = () => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();

    if (rect.bottom < NAVBAR_HEIGHT) {
      setOpen(false);
      setShowCustom(false);
      return;
    }

    setMenuPos({
      top: Math.max(NAVBAR_HEIGHT, rect.bottom + 8),
      left: rect.left,
      width: rect.width,
    });
  };

  useEffect(() => {
    if (open) {
      updatePosition();
      const handleScroll = () => updatePosition();
      window.addEventListener("scroll", handleScroll, true);
      window.addEventListener("resize", handleScroll);
      return () => {
        window.removeEventListener("scroll", handleScroll, true);
        window.removeEventListener("resize", handleScroll);
      };
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;

    function handleClick(e) {
      const clickedTrigger = triggerRef.current && triggerRef.current.contains(e.target);
      const clickedMenu = menuRef.current && menuRef.current.contains(e.target);

      if (!clickedTrigger && !clickedMenu) {
        setOpen(false);
        setShowCustom(false);
      }
    }

    const timer = setTimeout(() => {
      document.addEventListener("mousedown", handleClick);
    }, 100);

    return () => {
      clearTimeout(timer);
      document.removeEventListener("mousedown", handleClick);
    };
  }, [open]);

  useEffect(() => {
    function handleKey(e) {
      if (e.key === "Escape" && open) {
        setOpen(false);
        setShowCustom(false);
      }
    }
    if (open) {
      document.addEventListener("keydown", handleKey);
      return () => document.removeEventListener("keydown", handleKey);
    }
  }, [open]);

  const getSelectedLabel = () => {
    if (value?.startsWith("custom-")) {
      const parts = value.replace("custom-", "").split("-to-");
      if (parts.length === 2) {
        const start = new Date(parts[0]);
        const end = new Date(parts[1]);
        return `${formatDate(start)} → ${formatDate(end)}`;
      }
    }
    const selected = options.find((o) => o.value === value);
    return selected?.label || "Select...";
  };

  const formatDate = (d) => {
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  const handleSelect = (val) => {
    if (val === "custom") {
      setShowCustom(true);
      const today = new Date();
      const monthAgo = new Date(today);
      monthAgo.setDate(today.getDate() - 30);
      setCustomEnd(today.toISOString().split("T")[0]);
      setCustomStart(monthAgo.toISOString().split("T")[0]);
      setActivePreset("month");
      return;
    }
    if (onChange) onChange(val);
    setOpen(false);
    setShowCustom(false);
  };

  const applyPreset = (days, key) => {
    const t = new Date();
    const s = new Date(t);
    s.setDate(t.getDate() - (days - 1));
    setCustomStart(s.toISOString().split("T")[0]);
    setCustomEnd(t.toISOString().split("T")[0]);
    setActivePreset(key);
  };

  const handleApplyCustom = () => {
    if (!customStart || !customEnd) return;
    const startDate = new Date(customStart);
    const endDate = new Date(customEnd);
    if (startDate > endDate) return;
    const customValue = `custom-${customStart}-to-${customEnd}`;
    if (onChange) onChange(customValue);
    setOpen(false);
    setShowCustom(false);
  };

  const isCustomValid = () => {
    if (!customStart || !customEnd) return false;
    return new Date(customStart) <= new Date(customEnd);
  };

  const getDayCount = () => {
    if (!isCustomValid()) return 0;
    return Math.ceil((new Date(customEnd) - new Date(customStart)) / (1000 * 60 * 60 * 24)) + 1;
  };

  const maxDate = new Date().toISOString().split("T")[0];

  const presets = [
    { key: "7d", label: "7 Days", days: 7 },
    { key: "14d", label: "14 Days", days: 14 },
    { key: "month", label: "1 Month", days: 30 },
    { key: "3m", label: "3 Months", days: 90 },
  ];

  const handleTriggerClick = (e) => {
    e.stopPropagation();
    setOpen((prev) => !prev);
  };

  const showCustomRangeOption = options.some(o =>
    o.value === "7days" || o.value === "30days" || o.value === "90days"
  );

  return (
    <div className="an-dropdown">
      <button
        ref={triggerRef}
        type="button"
        className={`an-dropdown-trigger ${open ? "an-dropdown-trigger--open" : ""}`}
        onClick={handleTriggerClick}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span className="an-dropdown-label">{getSelectedLabel()}</span>
        <motion.span
          className="an-dropdown-chevron"
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.2, ease: [0.32, 0.72, 0, 1] }}
        >
          <ChevronDown size={14} />
        </motion.span>
      </button>

      {createPortal(
        <AnimatePresence>
          {open && (
            <div
              ref={menuRef}
              style={{
                position: "fixed",
                top: menuPos.top,
                left: showCustom ? Math.max(20, menuPos.left - 100) : menuPos.left,
                minWidth: showCustom ? 340 : Math.max(menuPos.width, 180),
                zIndex: 9999,
              }}
            >
              <motion.div
                className={`an-dropdown-menu-portal ${showCustom ? "an-dropdown-menu-portal--custom" : ""}`}
                role="listbox"
                onMouseDown={(e) => e.stopPropagation()}
                initial={{ opacity: 0, y: -8, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -6, scale: 0.97 }}
                transition={{ duration: 0.22, ease: [0.32, 0.72, 0, 1] }}
              >
                <AnimatePresence mode="wait">
                  {!showCustom ? (
                    <motion.div
                      key="options"
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      transition={{ duration: 0.18, ease: [0.32, 0.72, 0, 1] }}
                    >
                      {options.map((opt) => {
                        const isActive = opt.value === value && !value?.startsWith("custom-");
                        return (
                          <button
                            key={opt.value}
                            type="button"
                            role="option"
                            aria-selected={isActive}
                            className={`an-dropdown-item ${isActive ? "an-dropdown-item--active" : ""}`}
                            onClick={() => handleSelect(opt.value)}
                          >
                            <span className="an-dropdown-item-label">{opt.label}</span>
                            {isActive && (
                              <motion.span
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                className="an-dropdown-check"
                              >
                                <Check size={13} />
                              </motion.span>
                            )}
                          </button>
                        );
                      })}

                      {showCustomRangeOption && (
                        <>
                          <div className="an-dropdown-divider" />
                          <button
                            type="button"
                            className={`an-dropdown-item an-dropdown-item--custom ${value?.startsWith("custom-") ? "an-dropdown-item--active" : ""}`}
                            onClick={() => handleSelect("custom")}
                          >
                            <span className="an-dropdown-item-icon">
                              <Calendar size={14} strokeWidth={2.5} />
                            </span>
                            <span className="an-dropdown-item-label">Custom Range</span>
                            <motion.span
                              className="an-dropdown-item-chevron"
                              whileHover={{ x: 3 }}
                            >
                              <ArrowRight size={13} strokeWidth={2.5} />
                            </motion.span>
                          </button>
                        </>
                      )}
                    </motion.div>
                  ) : (
                    <motion.div
                      key="custom"
                      className="an-custom-panel"
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ duration: 0.22, ease: [0.32, 0.72, 0, 1] }}
                    >
                      <div className="an-custom-header">
                        <motion.button
                          className="an-custom-back"
                          onClick={() => setShowCustom(false)}
                          whileHover={{ x: -2 }}
                          whileTap={{ scale: 0.95 }}
                        >
                          <ArrowLeft size={13} strokeWidth={2.5} />
                        </motion.button>
                        <div className="an-custom-title-wrap">
                          <span className="an-custom-title">Custom Range</span>
                          <span className="an-custom-subtitle">Pick your date range</span>
                        </div>
                        {isCustomValid() && (
                          <motion.div
                            className="an-custom-day-badge"
                            initial={{ opacity: 0, scale: 0.7 }}
                            animate={{ opacity: 1, scale: 1 }}
                            key={getDayCount()}
                            transition={{ duration: 0.2, ease: [0.32, 0.72, 0, 1] }}
                          >
                            {getDayCount()}d
                          </motion.div>
                        )}
                      </div>

                      <div className="an-custom-presets">
                        {presets.map((p, i) => (
                          <motion.button
                            key={p.key}
                            className={`an-custom-preset ${activePreset === p.key ? "an-custom-preset--active" : ""}`}
                            onClick={() => applyPreset(p.days, p.key)}
                            whileHover={{ y: -1 }}
                            whileTap={{ scale: 0.96 }}
                            initial={{ opacity: 0, y: 6 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.05 + i * 0.03, duration: 0.25 }}
                          >
                            {p.label}
                          </motion.button>
                        ))}
                      </div>

                      <div className="an-custom-divider">
                        <span className="an-custom-divider-line" />
                        <span className="an-custom-divider-text">OR CHOOSE DATES</span>
                        <span className="an-custom-divider-line" />
                      </div>

                      <div className="an-custom-dates">
                        <motion.div
                          className="an-custom-date-card"
                          initial={{ opacity: 0, y: 4 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: 0.15, duration: 0.25 }}
                        >
                          <div className="an-custom-date-header">
                            <div className="an-custom-date-dot an-custom-date-dot--start" />
                            <span className="an-custom-date-label">FROM</span>
                          </div>
                          <input
                            type="date"
                            className="an-custom-date-input"
                            value={customStart}
                            max={customEnd || maxDate}
                            onChange={(e) => {
                              setCustomStart(e.target.value);
                              setActivePreset(null);
                            }}
                          />
                          {customStart && (
                            <div className="an-custom-date-display">
                              {new Date(customStart).toLocaleDateString("en-US", {
                                weekday: "short",
                                month: "long",
                                day: "numeric",
                                year: "numeric",
                              })}
                            </div>
                          )}
                        </motion.div>

                        <div className="an-custom-connector">
                          <div className="an-custom-connector-line" />
                          <motion.div
                            className="an-custom-connector-arrow"
                            animate={{ y: [0, 3, 0] }}
                            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                          >
                            <ArrowRight size={14} strokeWidth={2.5} style={{ transform: "rotate(90deg)" }} />
                          </motion.div>
                          <div className="an-custom-connector-line" />
                        </div>

                        <motion.div
                          className="an-custom-date-card"
                          initial={{ opacity: 0, y: 4 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: 0.2, duration: 0.25 }}
                        >
                          <div className="an-custom-date-header">
                            <div className="an-custom-date-dot an-custom-date-dot--end" />
                            <span className="an-custom-date-label">TO</span>
                          </div>
                          <input
                            type="date"
                            className="an-custom-date-input"
                            value={customEnd}
                            min={customStart}
                            max={maxDate}
                            onChange={(e) => {
                              setCustomEnd(e.target.value);
                              setActivePreset(null);
                            }}
                          />
                          {customEnd && (
                            <div className="an-custom-date-display">
                              {new Date(customEnd).toLocaleDateString("en-US", {
                                weekday: "short",
                                month: "long",
                                day: "numeric",
                                year: "numeric",
                              })}
                            </div>
                          )}
                        </motion.div>
                      </div>

                      <motion.button
                        className="an-custom-apply"
                        onClick={handleApplyCustom}
                        disabled={!isCustomValid()}
                        whileHover={isCustomValid() ? { y: -1 } : {}}
                        whileTap={isCustomValid() ? { scale: 0.98 } : {}}
                        transition={{ duration: 0.18, ease: [0.32, 0.72, 0, 1] }}
                      >
                        <span>Apply Range</span>
                        <ArrowRight size={14} strokeWidth={2.5} />
                      </motion.button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            </div>
          )}
        </AnimatePresence>,
        document.body
      )}
    </div>
  );
}