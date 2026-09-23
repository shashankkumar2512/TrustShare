import { useState } from 'react';
import { signup as signupService } from '../services/signup';
import { useAnalytics } from '../../../context/AnalyticsContext';

/**
 * useSignup — handles signup state, loading, and error management
 * @returns {{ signup: function, loading: boolean, error: string|null }}
 */
export const useSignup = () => {
  const { trackEvent } = useAnalytics();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const signup = async ({ name, email, password }) => {
    setLoading(true);
    setError(null);
    try {
      const data = await signupService({ name, email, password });
      trackEvent('signup_success', { email });
      return data;
    } catch (err) {
      setError(err.message || 'Signup failed. Please try again.');
      trackEvent('signup_error', { email });
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { signup, loading, error };
};
