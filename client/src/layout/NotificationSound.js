// client/src/layout/NotificationSound.js
/**
 * Plays a subtle notification sound when new notifications arrive.
 * Uses Web Audio API — no external sound files needed.
 */

import { useEffect, useRef } from "react";

// Generate a subtle notification chime using Web Audio API
function playNotificationSound() {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

    // First tone (higher)
    const osc1 = audioCtx.createOscillator();
    const gain1 = audioCtx.createGain();
    osc1.connect(gain1);
    gain1.connect(audioCtx.destination);
    osc1.type = "sine";
    osc1.frequency.setValueAtTime(880, audioCtx.currentTime); // A5
    gain1.gain.setValueAtTime(0.08, audioCtx.currentTime);
    gain1.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.3);
    osc1.start(audioCtx.currentTime);
    osc1.stop(audioCtx.currentTime + 0.3);

    // Second tone (lower, slightly delayed)
    const osc2 = audioCtx.createOscillator();
    const gain2 = audioCtx.createGain();
    osc2.connect(gain2);
    gain2.connect(audioCtx.destination);
    osc2.type = "sine";
    osc2.frequency.setValueAtTime(1320, audioCtx.currentTime + 0.1); // E6
    gain2.gain.setValueAtTime(0, audioCtx.currentTime);
    gain2.gain.setValueAtTime(0.06, audioCtx.currentTime + 0.1);
    gain2.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.4);
    osc2.start(audioCtx.currentTime + 0.1);
    osc2.stop(audioCtx.currentTime + 0.4);

    // Cleanup
    setTimeout(() => audioCtx.close(), 1000);
  } catch (e) {
    // Silent fail — some browsers block audio without user interaction
  }
}

export default function NotificationSound({ count = 0 }) {
  const prevCount = useRef(count);

  useEffect(() => {
    // Play sound only when count INCREASES (new notification arrived)
    if (count > prevCount.current && prevCount.current >= 0) {
      playNotificationSound();
    }
    prevCount.current = count;
  }, [count]);

  return null;
}