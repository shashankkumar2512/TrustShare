import React, { useState } from 'react';
import FormInput from '../../../components/Form/FormInput';
import { useAnalytics } from '../../../context/AnalyticsContext';
import { login } from '../services/login';

const LoginForm = ({ onSuccess }) => {
  const { trackEvent } = useAnalytics();
  const [form, setForm] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [serverError, setServerError] = useState('');

  const validate = () => {
    const errs = {};
    if (!form.email) errs.email = 'Email is required';
    else if (!/\S+@\S+\.\S+/.test(form.email)) errs.email = 'Invalid email format';
    if (!form.password) errs.password = 'Password is required';
    return errs;
  };

  const handleChange = (e) => {
    const { id, value } = e.target;
    setForm((prev) => ({ ...prev, [id]: value }));
    setErrors((prev) => ({ ...prev, [id]: '' }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) return setErrors(errs);
    setLoading(true);
    setServerError('');
    try {
      const data = await login(form.email, form.password);
      trackEvent('login_success', { email: form.email });
      onSuccess?.(data);
    } catch (err) {
      setServerError(err.message || 'Login failed. Please try again.');
      trackEvent('login_error', { email: form.email });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} noValidate>
      <FormInput id="email" label="Email" type="email" value={form.email} onChange={handleChange} error={errors.email} required placeholder="you@example.com" />
      <FormInput id="password" label="Password" type="password" value={form.password} onChange={handleChange} error={errors.password} required placeholder="••••••••" />
      {serverError && <p style={{ color: 'var(--danger)', fontSize: '13px', marginBottom: '12px' }}>{serverError}</p>}
      <button type="submit" disabled={loading} style={{ width: '100%', padding: '12px', background: 'var(--primary)', color: '#fff', border: 'none', borderRadius: '8px', fontWeight: 600, fontSize: '15px', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 }}>
        {loading ? 'Signing in…' : 'Sign In'}
      </button>
    </form>
  );
};

export default LoginForm;
