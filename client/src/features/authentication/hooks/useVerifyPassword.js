import { useState } from 'react';

/**
 * useVerifyPassword — validates password strength and match
 * @returns {{ verifyStrength: function, verifyMatch: function, strength: string }}
 */
export const useVerifyPassword = () => {
  const [strength, setStrength] = useState('');

  const verifyStrength = (password) => {
    if (!password) return setStrength('');
    if (password.length < 6) return setStrength('weak');
    const hasUpper = /[A-Z]/.test(password);
    const hasNumber = /\d/.test(password);
    const hasSymbol = /[^a-zA-Z0-9]/.test(password);
    if (password.length >= 12 && hasUpper && hasNumber && hasSymbol) return setStrength('strong');
    if (password.length >= 8 && (hasNumber || hasSymbol)) return setStrength('medium');
    return setStrength('weak');
  };

  const verifyMatch = (password, confirmPassword) => {
    return password === confirmPassword;
  };

  return { strength, verifyStrength, verifyMatch };
};
