// client/src/layout/LoadingBar.js
/**
 * Page loading progress bar — thin blue line at top.
 */

import React, { useState, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import "./LoadingBar.css";

export default function LoadingBar() {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const location = useLocation();
  const timerRef = useRef(null);

  useEffect(() => {
    // Start loading on route change
    setLoading(true);
    setProgress(0);

    // Simulate progress
    let current = 0;
    timerRef.current = setInterval(() => {
      current += Math.random() * 15 + 5;
      if (current > 90) current = 90;
      setProgress(current);
    }, 100);

    // Complete after short delay (page rendered)
    const completeTimer = setTimeout(() => {
      if (timerRef.current) clearInterval(timerRef.current);
      setProgress(100);
      setTimeout(() => setLoading(false), 200);
    }, 400);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      clearTimeout(completeTimer);
    };
  }, [location.pathname]);

  return (
    <AnimatePresence>
      {loading && (
        <motion.div
          className="loading-bar"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
        >
          <motion.div
            className="loading-bar-fill"
            initial={{ width: "0%" }}
            animate={{ width: `${progress}%` }}
            transition={{
              duration: 0.3,
              ease: [0.32, 0.72, 0, 1],
            }}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}