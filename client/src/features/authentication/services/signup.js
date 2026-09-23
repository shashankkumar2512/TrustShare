import { API_BASE_URL } from '../../../data/constants';

/**
 * signup — registers a new user
 * @param {{ name: string, email: string, password: string }} userData
 * @returns {Promise<{access_token: string, user: object}>}
 */
export const signup = async ({ name, email, password }) => {
  const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Signup failed');
  }

  return response.json();
};
