import React, { createContext, useContext, useState, useCallback } from 'react';

const AnalyticsContext = createContext(null);

/**
 * AnalyticsProvider — tracks page views and custom events
 */
export const AnalyticsProvider = ({ children }) => {
  const [events, setEvents] = useState([]);

  const trackEvent = useCallback((eventName, properties = {}) => {
    const event = {
      name: eventName,
      properties,
      timestamp: new Date().toISOString(),
    };
    setEvents((prev) => [...prev, event]);
    // TODO: Send to analytics backend
    console.log('[Analytics]', event);
  }, []);

  const trackPageView = useCallback((page) => {
    trackEvent('page_view', { page });
  }, [trackEvent]);

  return (
    <AnalyticsContext.Provider value={{ events, trackEvent, trackPageView }}>
      {children}
    </AnalyticsContext.Provider>
  );
};

/**
 * Custom hook to consume analytics context
 */
export const useAnalytics = () => {
  const ctx = useContext(AnalyticsContext);
  if (!ctx) throw new Error('useAnalytics must be used inside <AnalyticsProvider>');
  return ctx;
};

export default AnalyticsContext;
