/**
 * formatDate — formats a date value into a readable string
 * @param {string|Date|number} date - Date input
 * @param {object} options - Intl.DateTimeFormat options
 * @param {string} locale - Locale (default: 'en-US')
 * @returns {string} Formatted date string
 */
export const formatDate = (date, options = {}, locale = 'en-US') => {
  if (!date) return '—';
  const dateObj = new Date(date);
  if (isNaN(dateObj)) return 'Invalid date';
  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...options,
  }).format(dateObj);
};

/**
 * formatDateTime — formats date with time
 */
export const formatDateTime = (date, locale = 'en-US') => {
  return formatDate(date, { hour: '2-digit', minute: '2-digit' }, locale);
};

/**
 * timeAgo — returns a relative time string (e.g., "2 hours ago")
 * @param {string|Date|number} date
 * @returns {string}
 */
export const timeAgo = (date) => {
  if (!date) return '—';
  const seconds = Math.floor((Date.now() - new Date(date).getTime()) / 1000);
  const intervals = [
    { label: 'year', seconds: 31536000 },
    { label: 'month', seconds: 2592000 },
    { label: 'week', seconds: 604800 },
    { label: 'day', seconds: 86400 },
    { label: 'hour', seconds: 3600 },
    { label: 'minute', seconds: 60 },
  ];
  for (const interval of intervals) {
    const count = Math.floor(seconds / interval.seconds);
    if (count >= 1) return `${count} ${interval.label}${count > 1 ? 's' : ''} ago`;
  }
  return 'just now';
};
