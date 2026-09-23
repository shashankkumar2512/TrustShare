
import React from "react";
import { useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Sun, Moon } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import "./ThemeToggle.css";

// Routes where the navbar already has a theme toggle
const HIDDEN_ROUTES = [
  "/dashboard",
  "/files",
  "/my-files",
  "/sharing",
  "/shared-with-me",
  "/activity",
  "/analytics",
  "/notifications",
  "/admin",
  "/settings",
];

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();

  const shouldHide = HIDDEN_ROUTES.some((route) =>
    location.pathname.startsWith(route)
  );

  if (shouldHide) return null;

  return (
    <motion.button
      className="theme-toggle-floating"
      onClick={toggleTheme}
      initial={{ opacity: 0, scale: 0.8, y: -10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      whileHover={{ scale: 1.08, y: -2 }}
      whileTap={{ scale: 0.92 }}
      transition={{ duration: 0.25, ease: [0.32, 0.72, 0, 1] }}
      aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
      title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
    >
      <AnimatePresence mode="wait" initial={false}>
        {theme === "light" ? (
          <motion.span
            key="moon"
            initial={{ rotate: -90, opacity: 0, scale: 0.5 }}
            animate={{ rotate: 0,   opacity: 1, scale: 1   }}
            exit={{    rotate: 90,  opacity: 0, scale: 0.5 }}
            transition={{ duration: 0.3, ease: [0.32, 0.72, 0, 1] }}
            className="theme-toggle-icon"
          >
            <Moon size={18} />
          </motion.span>
        ) : (
          <motion.span
            key="sun"
            initial={{ rotate: 90,  opacity: 0, scale: 0.5 }}
            animate={{ rotate: 0,   opacity: 1, scale: 1   }}
            exit={{    rotate: -90, opacity: 0, scale: 0.5 }}
            transition={{ duration: 0.3, ease: [0.32, 0.72, 0, 1] }}
            className="theme-toggle-icon"
          >
            <Sun size={18} />
          </motion.span>
        )}
      </AnimatePresence>
    </motion.button>
  );
}
