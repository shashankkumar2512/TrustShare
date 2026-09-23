import React, { useState } from 'react';
import FormInput from '../../../components/Form/FormInput';
import { useSignup } from '../hooks/useSignup';

const SignupForm = ({ onSuccess }) => {
  const { signup, loading, error: signupError } = useSignup();
  const [form, setForm] = useState({ name: '', email: '', password: '', confirmPassword: '' });
  const [errors, setErrors] = useState({});

  const validate = () => {
    const errs = {};
    if (!form.name.trim()) errs.name = 'Full name is required';
    if (!form.email) errs.email = 'Email is required';
    else if (!/\S+@\S+\.\S+/.test(form.email)) errs.email = 'Invalid email format';
    if (!form.password) errs.password = 'Password is required';
    else if (form.password.length < 8) errs.password = 'Password must be at least 8 characters';
    if (form.confirmPassword !== form.password) errs.confirmPassword = 'Passwords do not match';
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
    const data = await signup({ name: form.name, email: form.email, password: form.password });
    if (data) onSuccess?.(data);
  };

  return (
    <form onSubmit={handleSubmit} noValidate>
      <FormInput id="name" label="Full Name" value={form.name} onChange={handleChange} error={errors.name} required placeholder="Jane Doe" />
      <FormInput id="email" label="Email" type="email" value={form.email} onChange={handleChange} error={errors.email} required placeholder="you@example.com" />
      <FormInput id="password" label="Password" type="password" value={form.password} onChange={handleChange} error={errors.password} required placeholder="Min 8 characters" />
      <FormInput id="confirmPassword" label="Confirm Password" type="password" value={form.confirmPassword} onChange={handleChange} error={errors.confirmPassword} required placeholder="Re-enter password" />
      {signupError && <p style={{ color: 'var(--danger)', fontSize: '13px', marginBottom: '12px' }}>{signupError}</p>}
      <button type="submit" disabled={loading} style={{ width: '100%', padding: '12px', background: 'var(--primary)', color: '#fff', border: 'none', borderRadius: '8px', fontWeight: 600, fontSize: '15px', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 }}>
        {loading ? 'Creating account…' : 'Create Account'}
      </button>
    </form>
  );
};

export default SignupForm;
