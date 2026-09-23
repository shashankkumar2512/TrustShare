// client/src/features/analytics/components/shared/EmptyState.js

import React from "react";
import { Inbox } from "lucide-react";

export default function EmptyState({ message = "No data available." }) {
  return (
    <div className="an-empty">
      <Inbox size={28} className="an-empty-icon" />
      <p className="an-empty-text">{message}</p>
    </div>
  );
}