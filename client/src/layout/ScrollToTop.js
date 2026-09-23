import { useEffect } from "react";
import { useLocation } from "react-router-dom";

/**
 * Auto-scroll to top when route changes.
 * Uses multiple techniques for reliability.
 */
export default function ScrollToTop() {
  const { pathname } = useLocation();

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    // Function to scroll everything
    const scrollAll = () => {
      const behavior = prefersReducedMotion ? "auto" : "smooth";

      // Window scroll
      window.scrollTo({ top: 0, left: 0, behavior });

      // Document scroll (fallback)
      document.documentElement.scrollTop = 0;
      document.body.scrollTop = 0;

      // Any custom scroll containers
      [
        ".page-wrapper",
        ".main-area",
        ".page-container",
        ".app-shell",
      ].forEach((selector) => {
        const el = document.querySelector(selector);
        if (el && el.scrollTop > 0) {
          try {
            el.scrollTo({ top: 0, behavior });
          } catch (e) {
            el.scrollTop = 0;
          }
        }
      });
    };

    // Run immediately
    scrollAll();

    // Run again after React finishes rendering (double-tap for reliability)
    const timeout = setTimeout(scrollAll, 50);

    return () => clearTimeout(timeout);
  }, [pathname]);

  return null;
}