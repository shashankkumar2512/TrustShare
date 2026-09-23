/**
 * formatCurrency — formats a number as a currency string
 * @param {number} amount - Amount to format
 * @param {string} currency - ISO currency code (default: 'USD')
 * @param {string} locale - Locale string (default: 'en-US')
 * @returns {string} Formatted currency string
 */
export const formatCurrency = (amount, currency = 'USD', locale = 'en-US') => {
  if (amount == null || isNaN(amount)) return '—';
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
};

/**
 * parseCurrency — removes currency formatting and returns a number
 * @param {string} formatted - Formatted currency string
 * @returns {number}
 */
export const parseCurrency = (formatted) => {
  return parseFloat(formatted.replace(/[^0-9.-]+/g, ''));
};
