// client/src/layout/Breadcrumbs.js
/**
 * Auto-generated breadcrumbs from the current route.
 * Place inside PageHeader or at top of any page.
 *
 * Usage:
 *   <Breadcrumbs />
 *   <Breadcrumbs items={[{ label: "Custom", to: "/custom" }]} />
 */

import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { ChevronRight, Home } from "lucide-react";
import "./Breadcrumbs.css";

const ROUTE_LABELS = {
  dashboard: "Dashboard",
  files: "My Files",
  "my-files": "My Files",
  sharing: "Sharing",
  "shared-with-me": "Shared with Me",
  activity: "Activity",
  notifications: "Notifications",
  analytics: "Analytics",
  admin: "Admin",
  settings: "Settings",
  assistant: "AI Assistant",
  configuration: "Configuration",
};

export default function Breadcrumbs({ items }) {
  const location = useLocation();

  const [analyticsTab, setAnalyticsTab] = useState(
    sessionStorage.getItem("analytics_active_tab") === "security"
      ? "security"
      : "analytics"
  );

  // ── My Files folder path state ──
  const [myFilesPath, setMyFilesPath] = useState(() => {
    try {
      const saved = sessionStorage.getItem("my_files_folder_path");
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    const handleAnalyticsTabChange = (event) => {
      const nextTab = event.detail === "security" ? "security" : "analytics";
      setAnalyticsTab(nextTab);
    };
    const handleMyFilesPathChange = (event) => {
      setMyFilesPath(Array.isArray(event.detail) ? event.detail : []);
    };

    window.addEventListener("analytics-tab-changed", handleAnalyticsTabChange);
    window.addEventListener("my-files-path-changed", handleMyFilesPathChange);
    return () => {
      window.removeEventListener("analytics-tab-changed", handleAnalyticsTabChange);
      window.removeEventListener("my-files-path-changed", handleMyFilesPathChange);
    };
  }, []);

  useEffect(() => {
    if (location.pathname !== "/my-files" && myFilesPath.length > 0) {
      setMyFilesPath([]);
      try {
        sessionStorage.removeItem("my_files_folder_path");
      } catch { }
    }
  }, [location.pathname]);

  // Auto-generate from route if no custom items
  let breadcrumbs =
    items ||
    location.pathname
      .split("/")
      .filter(Boolean)
      .map((segment, i, arr) => ({
        label: ROUTE_LABELS[segment] || segment.replace(/-/g, " "),
        to: "/" + arr.slice(0, i + 1).join("/"),
      }));

  if (!items && location.pathname === "/analytics") {
    breadcrumbs = [
      ...breadcrumbs,
      {
        label: analyticsTab === "security" ? "Security" : "File Analytics",
        to: "/analytics",
      },
    ];
  }

  if (!items && location.pathname === "/my-files" && myFilesPath.length > 0) {
    
    breadcrumbs = breadcrumbs.map((crumb) => {
      if (crumb.to === "/my-files") {
        return {
          ...crumb,
          onClick: () => {
            window.dispatchEvent(new CustomEvent("my-files-goto-root"));
          },
        };
      }
      return crumb;
    });

    myFilesPath.forEach((folder, index) => {
      const isLastFolder = index === myFilesPath.length - 1;
      breadcrumbs.push({
        label: folder.name,
        to: "/my-files",
        onClick: isLastFolder
          ? undefined
          : () => {
            window.dispatchEvent(
              new CustomEvent("my-files-goto-folder", { detail: index })
            );
          },
      });
    });
  }

  if (breadcrumbs.length === 0) return null;

  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      <Link to="/dashboard" className="breadcrumbs-home" title="Dashboard">
        <Home size={13} />
      </Link>

      {breadcrumbs.map((crumb, i) => {
        const isLast = i === breadcrumbs.length - 1;
        return (
          <motion.div
            key={`${crumb.to}-${i}-${crumb.label}`}
            className="breadcrumbs-item"
            initial={{ opacity: 0, x: -4 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05, duration: 0.2 }}
          >
            <ChevronRight size={12} className="breadcrumbs-separator" />
            {isLast ? (
              <span className="breadcrumbs-current">{crumb.label}</span>
            ) : crumb.onClick ? (
              <button
                type="button"
                onClick={crumb.onClick}
                className="breadcrumbs-link"
                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, font: 'inherit' }}
              >
                {crumb.label}
              </button>
            ) : (
              <Link to={crumb.to} className="breadcrumbs-link">
                {crumb.label}
              </Link>
            )}
          </motion.div>
        );
      })}
    </nav>
  );
}