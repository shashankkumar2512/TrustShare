import React, { useState, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Clock, LogOut, RefreshCw } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import "./SessionTimeout.css";

function getTokenExpiry() {
  const token =
    localStorage.getItem("access_token") ||
    sessionStorage.getItem("access_token");
  if (!token) return null;

  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.exp ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
}

const WARNING_BEFORE_MS = 5 * 60 * 1000;

export default function SessionTimeout() {
  const [showWarning, setShowWarning] = useState(false);
  const [timeLeft, setTimeLeft] = useState(0);
  const [extending, setExtending] = useState(false);
  const { logout } = useAuth();

  const checkExpiry = useCallback(() => {
    const expiry = getTokenExpiry();
    if (!expiry) return;

    const now = Date.now();
    const remaining = expiry - now;

    if (remaining <= 0) {
      logout();
      return;
    }

    if (remaining <= WARNING_BEFORE_MS) {
      setShowWarning(true);
      setTimeLeft(Math.ceil(remaining / 1000));
    } else {
      setShowWarning(false);
    }
  }, [logout]);

  useEffect(() => {
    checkExpiry();
    const interval = setInterval(checkExpiry, 30000);
    return () => clearInterval(interval);
  }, [checkExpiry]);

  useEffect(() => {
    if (!showWarning || timeLeft <= 0) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          logout();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [showWarning, timeLeft, logout]);

  const handleExtend = async () => {
    setExtending(true);
    try {
      const refreshToken =
        localStorage.getItem("refresh_token") ||
        sessionStorage.getItem("refresh_token");

      if (refreshToken) {
        const { default: api } = await import("../utils/api");
        const { data } = await api.post("/api/auth/refresh", {
          refresh_token: refreshToken,
        });

        const storage = localStorage.getItem("refresh_token")
          ? localStorage
          : sessionStorage;

        if (data.access_token) {
          storage.setItem("access_token", data.access_token);
        }
        if (data.refresh_token) {
          storage.setItem("refresh_token", data.refresh_token);
        }

        setShowWarning(false);
      }
    } catch (err) {
      console.error("Failed to extend session:", err);
      logout();
    } finally {
      setExtending(false);
    }
  };

  const formatTime = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  return createPortal(
    <AnimatePresence>
      {showWarning && (
        <motion.div
          className="session-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <motion.div
            className="session-modal"
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.92 }}
            transition={{ duration: 0.25, ease: [0.32, 0.72, 0, 1] }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="session-modal-icon">
              <Clock size={24} />
            </div>

            <h3 className="session-modal-title">Session Expiring</h3>

            <p className="session-modal-text">
              Your session will expire in{" "}
              <span className="session-modal-timer">
                {formatTime(timeLeft)}
              </span>
            </p>

            <p className="session-modal-hint">
              Extend your session to stay logged in.
            </p>

            <div className="session-modal-actions">
              <motion.button
                className="session-btn session-btn--extend"
                onClick={handleExtend}
                disabled={extending}
                whileHover={{ y: -1 }}
                whileTap={{ scale: 0.98 }}
              >
                <RefreshCw
                  size={14}
                  className={extending ? "session-spin" : ""}
                />
                {extending ? "Extending..." : "Extend Session"}
              </motion.button>

              <motion.button
                className="session-btn session-btn--logout"
                onClick={logout}
                whileHover={{ y: -1 }}
                whileTap={{ scale: 0.98 }}
              >
                <LogOut size={14} />
                Log Out
              </motion.button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body
  );
}