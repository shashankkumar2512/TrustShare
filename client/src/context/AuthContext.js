import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authAPI } from '../utils/api';

const AuthContext = createContext(null);

// FIX ISS-D9: only wipe auth-related keys, preserve theme/settings/etc.
const AUTH_STORAGE_KEYS = ['access_token', 'refresh_token', 'user'];

const ASSISTANT_SESSION_KEYS = [
  'trustshare_bubble_conversation_id',
  'trustshare_bubble_open',
];

const clearAuthStorage = () => {
  AUTH_STORAGE_KEYS.forEach((k) => {
    localStorage.removeItem(k);
    sessionStorage.removeItem(k);
  });
  
  ASSISTANT_SESSION_KEYS.forEach((k) => {
    sessionStorage.removeItem(k);
  });
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Re-hydrate from localStorage or sessionStorage on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    if (token) {
      authAPI.me()
        .then(({ data }) => setUser(data))
        .catch(() => {
          clearAuthStorage();        // FIX ISS-D9: targeted clear
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (email, password, rememberMe = true) => {
    const { data } = await authAPI.login(email, password);
    // If MFA is required, we don't store tokens yet (backend won't return access_token/refresh_token)
    if (!data.mfa_required) {
      const storage = rememberMe ? localStorage : sessionStorage;
      storage.setItem('access_token', data.access_token);
      storage.setItem('refresh_token', data.refresh_token);
      setUser(data.user);
    }
    return data;
  }, []);

  const register = useCallback(async (name, email, password) => {
    const { data } = await authAPI.signup(name, email, password);
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(async () => {
    try { await authAPI.logout(); } catch {}
    clearAuthStorage();              // FIX ISS-D9: targeted clear
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  return ctx || { user: null, loading: false, login: () => {}, register: () => {}, logout: () => {} };
}
