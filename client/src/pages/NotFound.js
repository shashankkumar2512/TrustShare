import React from "react";
import { Link } from "react-router-dom";
import "./NotFound.css";

export default function NotFound() {
  return (
    <div className="not-found">

      <div className="not-found-card">

        <h1 className="not-found-code">
          404
        </h1>

        <h2 className="not-found-title">
          Page Not Found
        </h2>

        <p className="not-found-description">
          The page you are looking for doesn't exist or may have been moved.
        </p>

        <Link
          to="/dashboard"
          className="not-found-btn"
        >
          ← Back to Dashboard
        </Link>

      </div>
    </div>
  );
}