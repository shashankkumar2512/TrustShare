import React, { useState } from "react";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";
import PageContainer from "./PageContainer";
import ScrollToTopButton from "./ScrollToTopButton";
import ConnectionStatus from "./ConnectionStatus";
import SessionTimeout from "./SessionTimeout";
import LoadingBar from "./LoadingBar";
import KeyboardShortcuts from "./KeyboardShortcuts";
import FaviconBadge from "./FaviconBadge";
import NotificationSound from "./NotificationSound";
import "./Layout.css";

export default function Layout({ children, unreadCount = 0 }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(
    localStorage.getItem("sidebar-collapsed") === "true"
  );

  const handleToggleCollapse = (value) => {
    setSidebarCollapsed(value);
    localStorage.setItem("sidebar-collapsed", value);
  };

  return (
    <div className="app-shell">
      {/* Global utilities */}
      <LoadingBar />
      <SessionTimeout />
      <KeyboardShortcuts />
      <FaviconBadge count={unreadCount} />
      <NotificationSound count={unreadCount} />

      <Sidebar
        unreadCount={unreadCount}
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        sidebarCollapsed={sidebarCollapsed}
        setSidebarCollapsed={handleToggleCollapse}
      />

      <div
        className={`main-area ${sidebarCollapsed ? "main-area-collapsed" : ""}`}
      >
        <Navbar
          unreadCount={unreadCount}
          setSidebarOpen={setSidebarOpen}
          connectionStatus={<ConnectionStatus />}
        />
        <PageContainer>{children}</PageContainer>
      </div>

      <ScrollToTopButton />
    </div>
  );
}