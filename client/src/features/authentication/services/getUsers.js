import { API_BASE_URL } from '../../../data/constants';

/**
 * getUsers — fetches list of users from the API
 * @param {string} token - Auth token
 * @returns {Promise<Array>} List of users
 */
export const getUsers = async (token) => {
  const response = await fetch(`${API_BASE_URL}/api/users`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch users');
  }

  return response.json();
};
