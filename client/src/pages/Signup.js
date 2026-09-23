import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { User, Mail, Lock, Eye, EyeOff, ArrowRight, ArrowLeft, Check, Server, Award, Sun, Moon } from 'lucide-react';
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

export default function Signup() {
  const { register } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({ name: '', email: '', password: '', confirmPassword: '' });
  const [error, setError] = useState('');
  const [fe, setFe] = useState({});
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);
  const [mouseX, setMouseX] = useState(0);
  const [mouseY, setMouseY] = useState(0);

  useEffect(() => {
    const fn = (e) => { setMouseX(e.clientX); setMouseY(e.clientY); };
    window.addEventListener('mousemove', fn);
    return () => window.removeEventListener('mousemove', fn);
  }, []);

  const str = (() => { const p = form.password; let s = 0; if (p.length >= 8) s++; if (/[A-Z]/.test(p)) s++; if (/[0-9]/.test(p)) s++; if (/[^A-Za-z0-9]/.test(p)) s++; return s; })();
  const sL = ['', 'Weak', 'Fair', 'Good', 'Strong'][str];
  const sC = ['', '#ff3b30', '#ff9500', '#0071e3', '#34c759'][str];

  const next = () => {
    const e = {};
    if (step === 1 && !form.name.trim()) e.name = 'Required';
    if (step === 2) { if (!form.email) e.email = 'Required'; else if (!/\S+@\S+\.\S+/.test(form.email)) e.email = 'Invalid'; }
    if (step === 3) { if (!form.password) e.password = 'Required'; else if (form.password.length < 8) e.password = 'Min 8 chars'; if (form.confirmPassword !== form.password) e.cp = 'No match'; }
    setFe(e); if (Object.keys(e).length) return;
    if (step < 3) setStep(step + 1); else doSubmit();
  };

  const doSubmit = async () => {
    setError(''); setLoading(true);
    try { await register(form.name, form.email, form.password); navigate('/dashboard'); }
    catch (err) { setError(err.response?.data?.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  const labels = ['Name', 'Email', 'Password'];

  return (
    <div className="ap">
      <BgEnvironment mouseX={mouseX} mouseY={mouseY} />

      <nav className="ap-nav">
        <Link to="/login" className="ap-logo">
          <img src="/logo.png" alt="" onError={e => e.target.style.display='none'} />
          TrustShare
        </Link>
        <div className="ap-nav-r">
          <Link to="/login" className="ap-nav-a ap-nav-cta">Sign In</Link>
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
          
          <motion.div 
            className="ap-auth-side-narrative"
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, ease: [0.16,1,0.3,1] }}
          >
            <span className="ap-narrative-eyebrow" style={{ color: 'var(--purple)', background: 'var(--purple-g)', borderColor: 'rgba(175,82,222,0.15)' }}>Dynamic Setup</span>
            <h1 className="ap-narrative-h1">
              Create your<br /><span className="italic-gradient">secure account.</span>
            </h1>
            <p className="ap-narrative-p">
              Provision decentralized encryption containers in 30 seconds. All file uploads are protected with unique rotating vault keys automatically.
            </p>
            <div className="ap-narrative-features">
              {[
                { t: '99.99% Guaranteed Operational SLA', i: Server },
                { t: 'Compliance standard SOC 2 validated', i: Award }
              ].map((f, i) => (
                <div key={i} className="ap-narrative-feat">
                  <div className="ap-narrative-feat-circle" style={{ background: 'rgba(175,82,222,0.08)', color: 'var(--purple)' }}><f.i size={12} /></div>
                  <span>{f.t}</span>
                </div>
              ))}
            </div>
          </motion.div>

          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <motion.div className="ap-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, ease: [0.16,1,0.3,1] }}>
              <div className="ap-card-head">
                <div className="ap-card-ic"><User size={24} /></div>
                <h2 className="ap-card-t">Sign up</h2>
                <p className="ap-card-s">Step {step} of 3 — {labels[step - 1]}</p>
              </div>

              <div className="ap-steps">
                {[1,2,3].map((s, i) => (
                  <React.Fragment key={s}>
                    <div className={`ap-step ${s === step ? 'on' : ''} ${s < step ? 'done' : ''}`}>
                      <div className="ap-step-d">{s < step ? <Check size={12} /> : s}</div>
                      <span className="ap-step-l">{labels[i]}</span>
                    </div>
                    {i < 2 && <div className="ap-step-line"><div className="ap-step-line-fill" style={{ width: s < step ? '100%' : '0%' }} /></div>}
                  </React.Fragment>
                ))}
              </div>

              {error && <div className="ap-berr">{error}</div>}

              <AnimatePresence mode="wait">
                <motion.div key={step} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.25 }}>
                  {step === 1 && (
                    <div className="ap-f"><div className="ap-fi">
                      <span className="ap-ic"><User size={16} /></span>
                      <input className="ap-in" type="text" placeholder="Full name" value={form.name} onChange={e => { setForm(f => ({...f, name: e.target.value})); setFe({}); }} autoFocus required />
                    </div>{fe.name && <div className="ap-err">{fe.name}</div>}</div>
                  )}
                  {step === 2 && (
                    <div className="ap-f"><div className="ap-fi">
                      <span className="ap-ic"><Mail size={16} /></span>
                      <input className="ap-in" type="email" placeholder="Work email" value={form.email} onChange={e => { setForm(f => ({...f, email: e.target.value})); setFe({}); }} autoFocus required />
                    </div>{fe.email && <div className="ap-err">{fe.email}</div>}</div>
                  )}
                  {step === 3 && (
                    <>
                      <div className="ap-f"><div className="ap-fi">
                        <span className="ap-ic"><Lock size={16} /></span>
                        <input className="ap-in" type={showPw ? 'text' : 'password'} placeholder="Password" value={form.password} onChange={e => { setForm(f => ({...f, password: e.target.value})); setFe({}); }} autoFocus required />
                        <button type="button" className="ap-tog" onClick={() => setShowPw(v => !v)}>{showPw ? <EyeOff size={15} /> : <Eye size={15} />}</button>
                      </div>{fe.password && <div className="ap-err">{fe.password}</div>}
                      {form.password && <div className="ap-str"><div className="ap-str-bar">{[1,2,3,4].map(i => (<div key={i} className="ap-str-s" style={{ background: i <= str ? sC : undefined }} />))}</div><div className="ap-str-t" style={{ color: sC }}>{sL}</div></div>}
                      </div>
                      <div className="ap-f"><div className="ap-fi">
                        <span className="ap-ic"><Lock size={16} /></span>
                        <input className="ap-in" type="password" placeholder="Confirm password" value={form.confirmPassword} onChange={e => { setForm(f => ({...f, confirmPassword: e.target.value})); setFe({}); }} required />
                      </div>{fe.cp && <div className="ap-err">{fe.cp}</div>}</div>
                    </>
                  )}
                </motion.div>
              </AnimatePresence>

              <div style={{ display: 'flex', gap: 8, marginTop: 20 }}>
                {step > 1 && <button className="ap-btn" type="button" onClick={() => setStep(step - 1)} style={{ width: 46, minWidth: 46, padding: 0, background: 'var(--input)', color: 'var(--t1)' }}><ArrowLeft size={16} /></button>}
                <button className="ap-btn" type="button" onClick={next} disabled={loading}>
                  {loading ? <><span className="ap-spin" /></> : step < 3 ? <>Continue <ArrowRight size={14} /></> : 'Create Account'}
                </button>
              </div>

              <div className="ap-foot">Already have an account? <Link to="/login" className="ap-a">Sign in</Link></div>
            </motion.div>
          </div>

        </div>
      </div>
    </div>
  );
}