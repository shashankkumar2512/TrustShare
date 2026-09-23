import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { authAPI } from '../utils/api';
import { Lock, Eye, EyeOff, Check, ShieldCheck, Key, Sun, Moon } from 'lucide-react';
import '../styles/apple-auth.css';

const BgEnvironment = ({ mouseX, mouseY }) => (
  <>
    <div className="ap-parallax-orb" style={{ left: mouseX, top: mouseY }} />
    <div className="ap-grain" />
    <div className="ap-env">
      <div className="ap-aurora">
        <div className="ap-ab" />
        <div className="ap-ab" />
        <div className="ap-ab" />
        <div className="ap-ab" />
      </div>
      <div className="ap-beams">
        <div className="ap-beam" />
        <div className="ap-beam" />
        <div className="ap-beam" />
      </div>
      <div className="ap-mesh">
        <div className="ap-mesh-grid" />
        <div className="ap-mesh-dots" />
      </div>
      <div className="ap-orbits">
        <div className="ap-orbit"><div className="ap-orbit-dot" /></div>
        <div className="ap-orbit"><div className="ap-orbit-dot" /></div>
        <div className="ap-orbit"><div className="ap-orbit-dot" /></div>
      </div>
      <div className="ap-shapes">
        <div className="ap-shape"><svg viewBox="0 0 60 60"><circle cx="30" cy="30" r="28" fill="none" stroke="rgba(0,113,227,0.3)" strokeWidth="1" /></svg></div>
        <div className="ap-shape"><svg viewBox="0 0 40 40"><polygon points="20,2 38,20 20,38 2,20" fill="none" stroke="rgba(175,82,222,0.3)" strokeWidth="1" /></svg></div>
        <div className="ap-shape"><svg viewBox="0 0 80 80"><polygon points="40,4 74,22 74,58 40,76 6,58 6,22" fill="none" stroke="rgba(255,55,95,0.25)" strokeWidth="1" /></svg></div>
      </div>
      <div className="ap-particles">
        {Array.from({ length: 25 }).map((_, i) => (
          <div key={i} className="ap-p" style={{
            left: `${(i * 13 + 7) % 100}%`,
            animationDuration: `${8 + (i % 10)}s`,
            animationDelay: `${(i * 1.1) % 12}s`,
            width: `${2 + (i % 4)}px`,
            height: `${2 + (i % 4)}px`,
          }} />
        ))}
      </div>
      <div className="ap-sparkles">
        {Array.from({ length: 15 }).map((_, i) => (
          <div key={i} className="ap-sparkle" style={{
            left: `${(i * 17 + 11) % 100}%`,
            top: `${(i * 23 + 9) % 100}%`,
            animationDelay: `${(i * 0.4) % 3}s`,
          }} />
        ))}
      </div>
    </div>
  </>
);

export default function ResetPassword() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ password: '', confirmPassword: '' });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const [fe, setFe] = useState({});
  const [showPw, setShowPw] = useState(false);
  const [showCPw, setShowCPw] = useState(false);
  const [mouseX, setMouseX] = useState(0);
  const [mouseY, setMouseY] = useState(0);
  const token = new URLSearchParams(location.search).get('token') || '';

  useEffect(() => {
    const fn = (e) => { setMouseX(e.clientX); setMouseY(e.clientY); };
    window.addEventListener('mousemove', fn);
    return () => window.removeEventListener('mousemove', fn);
  }, []);

  const str = (() => {
    const p = form.password;
    let s = 0;
    if (p.length >= 8) s++;
    if (/[A-Z]/.test(p)) s++;
    if (/[0-9]/.test(p)) s++;
    if (/[^A-Za-z0-9]/.test(p)) s++;
    return s;
  })();
  const sL = ['', 'Weak', 'Fair', 'Good', 'Strong'][str];
  const sC = ['', '#ff3b30', '#ff9500', '#0071e3', '#34c759'][str];

  const validate = () => {
    const e = {};
    if (!form.password) e.password = 'Required';
    else {
      if (form.password.length < 8) e.password = 'Min 8 characters';
      if (!/[A-Z]/.test(form.password)) e.password = 'One uppercase required';
      if (!/[0-9]/.test(form.password)) e.password = 'One number required';
      if (!/[^A-Za-z0-9]/.test(form.password)) e.password = 'One symbol required';
    }
    if (form.confirmPassword !== form.password) e.cp = 'Passwords do not match';
    setFe(e); return !Object.keys(e).length;
  };

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    if (!token) { setError('Reset token missing. Please request a new link.'); return; }
    if (!validate()) return;
    setLoading(true);
    try {
      await authAPI.resetPassword(token, form.password);
      setSuccess(true);
      setTimeout(() => navigate('/login'), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Password reset failed. The link may have expired.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ap">
      <BgEnvironment mouseX={mouseX} mouseY={mouseY} />

      <nav className="ap-nav">
        <Link to="/login" className="ap-logo">
          <img src="/logo.png" alt="" onError={e => e.target.style.display = 'none'} />
          TrustShare
        </Link>
        <div className="ap-nav-r">
          <Link to="/login" className="ap-nav-a">Sign In</Link>
          <div className="ap-nav-divider" />
          <button 
            type="button" 
            className="ap-theme-btn" 
            onClick={toggleTheme} 
            title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            aria-label="Toggle Theme"
          >
            {isDark ? <Sun size={15} /> : <Moon size={15} />}
          </button>
        </div>
      </nav>

      <div className="ap-auth-split-wrapper">
        <div className="ap-auth-inner-split">
          
          {/* LEFT NARRATIVE PANEL */}
          <motion.div 
            className="ap-auth-side-narrative"
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          >
            <span className="ap-narrative-eyebrow" style={{ color: 'var(--ok)', background: 'rgba(52,199,89,0.08)', borderColor: 'rgba(52,199,89,0.15)' }}>Credentials Update</span>
            <h1 className="ap-narrative-h1">
              Configure New<br /><span className="italic-gradient">Vault Master Key.</span>
            </h1>
            <p className="ap-narrative-p">
              Confirm your new account password. Our backend enforces strict entropy checks and automatically purges all active session tokens on submit.
            </p>
            <div className="ap-narrative-features">
              {[
                { t: 'Multi-device session token invalidation', i: ShieldCheck },
                { t: 'Bcrypt-based hashing with dynamic salt rounds', i: Key }
              ].map((f, i) => (
                <div key={i} className="ap-narrative-feat">
                  <div className="ap-narrative-feat-circle" style={{ background: 'rgba(52,199,89,0.08)', color: 'var(--ok)' }}><f.i size={12} /></div>
                  <span>{f.t}</span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* RIGHT NEW PASSWORD CARD */}
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <motion.div className="ap-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
              {success ? (
                <div style={{ textAlign: 'center' }}>
                  <div className="ap-card-ic" style={{ background: 'rgba(52,199,89,0.1)', color: 'var(--ok)' }}><Check size={24} /></div>
                  <h2 className="ap-card-t">Password updated</h2>
                  <p className="ap-card-s">All active sessions have been purged. Redirecting to sign in…</p>
                </div>
              ) : (
                <>
                  <div className="ap-card-head">
                    <div className="ap-card-ic"><Lock size={24} /></div>
                    <h2 className="ap-card-t">Reset password</h2>
                    <p className="ap-card-s">Create a new strong password.</p>
                  </div>

                  <form onSubmit={submit}>
                    <div className="ap-f"><div className="ap-fi">
                      <span className="ap-ic"><Lock size={16} /></span>
                      <input
                        className="ap-in"
                        type={showPw ? 'text' : 'password'}
                        placeholder="New password"
                        value={form.password}
                        onChange={e => { setForm(f => ({ ...f, password: e.target.value })); setFe(f => ({ ...f, password: '' })); }}
                        required
                      />
                      <button type="button" className="ap-tog" onClick={() => setShowPw(v => !v)}>{showPw ? <EyeOff size={15} /> : <Eye size={15} />}</button>
                    </div>{fe.password && <div className="ap-err">{fe.password}</div>}
                    {form.password && (
                      <div className="ap-str">
                        <div className="ap-str-bar">
                          {[1, 2, 3, 4].map(i => (<div key={i} className="ap-str-s" style={{ background: i <= str ? sC : undefined }} />))}
                        </div>
                        <div className="ap-str-t" style={{ color: sC }}>{sL}</div>
                      </div>
                    )}
                    </div>

                    <div className="ap-f"><div className="ap-fi">
                      <span className="ap-ic"><Lock size={16} /></span>
                      <input
                        className="ap-in"
                        type={showCPw ? 'text' : 'password'}
                        placeholder="Confirm password"
                        value={form.confirmPassword}
                        onChange={e => { setForm(f => ({ ...f, confirmPassword: e.target.value })); setFe(f => ({ ...f, cp: '' })); }}
                        required
                      />
                      <button type="button" className="ap-tog" onClick={() => setShowCPw(v => !v)}>{showCPw ? <EyeOff size={15} /> : <Eye size={15} />}</button>
                    </div>{fe.cp && <div className="ap-err">{fe.cp}</div>}</div>

                    {error && <div className="ap-berr">{error}</div>}

                    <button className="ap-btn" type="submit" disabled={loading} style={{ marginTop: 8 }}>
                      {loading ? <><span className="ap-spin" /> Updating…</> : 'Reset Password'}
                    </button>
                  </form>
                </>
              )}
            </motion.div>
          </div>

        </div>
      </div>
    </div>
  );
}