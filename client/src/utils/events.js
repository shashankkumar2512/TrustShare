// client/src/utils/events.js
/**
 * Simple event bus for cross-component communication.
 * Used to notify components when files are uploaded/deleted.
 */

const listeners = {};

export const events = {
  on(event, callback) {
    if (!listeners[event]) listeners[event] = [];
    listeners[event].push(callback);
    return () => this.off(event, callback);
  },

  off(event, callback) {
    if (!listeners[event]) return;
    listeners[event] = listeners[event].filter((cb) => cb !== callback);
  },

  emit(event, data) {
    if (!listeners[event]) return;
    listeners[event].forEach((cb) => cb(data));
  },
};

// Event constants
export const EVENTS = {
  FILE_UPLOADED: "file:uploaded",
  FILE_DELETED: "file:deleted",
  STORAGE_CHANGED: "storage:changed",
  MY_FILES_ROOT: "my-files:root",
  NOTIFICATIONS_CHANGED: "notifications:changed",
};
