// client/src/layout/ConnectionStatus.js
/**
 * Online/offline indicator — shows connection status in navbar.
 * Detects internet connectivity changes in real-time.
 */

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Wifi, WifiOff } from "lucide-react";
import "./ConnectionStatus.css";

export default function ConnectionStatus() {
    const [online, setOnline] = useState(navigator.onLine);
    const [showBanner, setShowBanner] = useState(false);

    useEffect(() => {
        const handleOnline = () => {
            setOnline(true);
            setShowBanner(true);
            setTimeout(() => setShowBanner(false), 3000);
        };

        const handleOffline = () => {
            setOnline(false);
            setShowBanner(true);
        };

        window.addEventListener("online", handleOnline);
        window.addEventListener("offline", handleOffline);

        return () => {
            window.removeEventListener("online", handleOnline);
            window.removeEventListener("offline", handleOffline);
        };
    }, []);

    return (
        <>
            {/* Small indicator dot in navbar */}
            <div
                className={`connection-dot ${online ? "connection-dot--online" : "connection-dot--offline"}`}
                title={online ? "Connected" : "No internet connection"}
            >
                {online ? <Wifi size={14} /> : <WifiOff size={14} />}
            </div>

            {/* Banner that shows on status change */}
            <AnimatePresence>
                {showBanner && (
                    <motion.div
                        className={`connection-banner ${online ? "connection-banner--online" : "connection-banner--offline"}`}
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.3, ease: [0.32, 0.72, 0, 1] }}
                    >
                        {online ? (
                            <>
                                <Wifi size={14} />
                                <span>Back online</span>
                            </>
                        ) : (
                            <>
                                <WifiOff size={14} />
                                <span>No internet connection</span>
                            </>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}