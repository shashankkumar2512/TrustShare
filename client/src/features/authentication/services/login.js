import { API_BASE_URL, LOCAL_STORAGE_KEYS } from '../../../data/constants';

/**
 * login — authenticates a user and stores the token
 * @param {string} email
 * @param {string} password
 * @returns {Promise<{access_token: string, user: object}>}
 */
export const login = async (email, password) => {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Invalid credentials');
  }

  const data = await response.json();

  // Persist token and user to localStorage
  localStorage.setItem(LOCAL_STORAGE_KEYS.AUTH_TOKEN, data.access_token);
  localStorage.setItem(LOCAL_STORAGE_KEYS.USER, JSON.stringify(data.user));

  return data;
};
