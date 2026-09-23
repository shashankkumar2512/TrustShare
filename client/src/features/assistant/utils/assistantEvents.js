const EVENT_NAME = 'trustshare-assistant-update';

/**
 * Emit an event when a chat action happens in the bubble.
 * @param {object} detail - { type: 'message_sent' | 'conversation_created', conversationId }
 */
export const emitAssistantEvent = (detail = {}) => {
  window.dispatchEvent(new CustomEvent(EVENT_NAME, { detail }));
};

/**
 * Subscribe to assistant events.
 * @param {function} handler - Called with the event detail
 * @returns {function} unsubscribe function
 */
export const onAssistantEvent = (handler) => {
  const wrapped = (e) => handler(e.detail);
  window.addEventListener(EVENT_NAME, wrapped);
  return () => window.removeEventListener(EVENT_NAME, wrapped);
};