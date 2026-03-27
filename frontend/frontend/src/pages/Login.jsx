import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'
import { loginUser } from '../api/client'

/* ── SVG Icons (inline, no dependency) ─────────────────────── */
const IconMail = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
    <rect x="2" y="4" width="20" height="16" rx="2"/>
    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
  </svg>
)

const IconLock = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
    <rect x="3" y="11" width="18" height="11" rx="2"/>
    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
  </svg>
)

const IconShield = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
  </svg>
)

const IconEye = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
    <circle cx="12" cy="12" r="3"/>
  </svg>
)

const IconEyeOff = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
    <line x1="1" y1="1" x2="23" y2="23"/>
  </svg>
)

const IconSun = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
    <circle cx="12" cy="12" r="5"/>
    <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
    <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
  </svg>
)

const IconMoon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
  </svg>
)

/* ── Feature list for the left panel ───────────────────────── */
const FEATURES = [
  { emoji: '📈', title: 'FIRE Path Planner',    desc: 'Project your path to financial independence' },
  { emoji: '🩺', title: 'Money Health Score',   desc: '6-dimension financial wellness score'         },
  { emoji: '🤖', title: 'AI Financial Advisor', desc: 'Answers powered by your real data'            },
  { emoji: '🧾', title: 'Tax Optimizer',         desc: 'Old vs new regime — maximize savings'         },
]

export default function Login() {
  const navigate = useNavigate()
  const { dark, toggle } = useTheme()

  const [form, setForm] = useState({ email: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [apiError, setApiError] = useState('')

  const update = (field) => (e) => {
    setForm(f => ({ ...f, [field]: e.target.value }))
    if (errors[field]) setErrors(er => ({ ...er, [field]: '' }))
    setApiError('')
  }

  const validate = () => {
    const errs = {}
    if (!form.email)    errs.email    = 'Email is required'
    else if (!/\S+@\S+\.\S+/.test(form.email)) errs.email = 'Enter a valid email'
    if (!form.password) errs.password = 'Password is required'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    try {
      const res = await loginUser({ email: form.email, password: form.password })
      localStorage.setItem('artha_token', res.data.access_token)
      navigate('/dashboard')
    } catch (err) {
      setApiError(err?.response?.data?.detail || 'Invalid credentials. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      {/* ── Left Panel ────────────────────────────────── */}
      <div className="auth-panel-left">
        <div style={{ position: 'relative', zIndex: 1, width: '100%', maxWidth: 420 }}>
          {/* Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 48 }}>
            <div style={{ width: 48, height: 48, background: 'rgba(255,255,255,0.2)', borderRadius: 14, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem', backdropFilter: 'blur(8px)', border: '1px solid rgba(255,255,255,0.3)' }}>₹</div>
            <span style={{ fontSize: '1.8rem', fontWeight: 800, color: '#fff', letterSpacing: '-0.03em' }}>Dinero</span>
          </div>

          <h2 style={{ color: '#fff', fontSize: '1.6rem', marginBottom: 12 }}>
            Your Personal Finance Mentor
          </h2>
          <p style={{ color: 'rgba(255,255,255,0.75)', marginBottom: 40, lineHeight: 1.7 }}>
            Built for everyday Indians who deserve professional-grade financial planning — for free.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {FEATURES.map(({ emoji, title, desc }) => (
              <div key={title} style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                <div style={{ width: 40, height: 40, background: 'rgba(255,255,255,0.15)', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.1rem', flexShrink: 0, backdropFilter: 'blur(4px)' }}>{emoji}</div>
                <div>
                  <div style={{ color: '#fff', fontWeight: 600, fontSize: '0.9rem' }}>{title}</div>
                  <div style={{ color: 'rgba(255,255,255,0.65)', fontSize: '0.8rem' }}>{desc}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Floating badge */}
          <div style={{ marginTop: 48, display: 'inline-flex', alignItems: 'center', gap: 8, background: 'rgba(255,255,255,0.15)', backdropFilter: 'blur(8px)', border: '1px solid rgba(255,255,255,0.25)', borderRadius: 9999, padding: '8px 16px' }}>
            <span style={{ color: '#86EFAC', fontSize: '0.75rem' }}>●</span>
            <span style={{ color: '#fff', fontSize: '0.8rem', fontWeight: 500 }}>Trusted by 50,000+ Indians</span>
          </div>
        </div>
      </div>

      {/* ── Right Panel ───────────────────────────────── */}
      <div className="auth-panel-right">
        <div className="auth-card">
          {/* Logo (mobile) */}
          <div className="auth-logo">
            <div className="auth-logo-icon">₹</div>
            <span className="auth-logo-text">Dinero</span>
          </div>

          <h1 className="auth-heading" style={{ fontSize: '1.6rem' }}>Welcome back</h1>
          <p className="auth-subheading">Sign in to your financial dashboard</p>

          {/* API Error */}
          {apiError && (
            <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)', borderRadius: 10, padding: '12px 14px', marginBottom: 18, color: '#EF4444', fontSize: '0.85rem', display: 'flex', gap: 8, alignItems: 'center' }}>
              ⚠️ {apiError}
            </div>
          )}

          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            {/* Email */}
            <div className="input-group">
              <label className="input-label" htmlFor="login-email">Email address</label>
              <div className="input-wrapper">
                <span className="input-icon"><IconMail /></span>
                <input
                  id="login-email"
                  type="email"
                  className={`input-field${errors.email ? ' error' : ''}`}
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={update('email')}
                  autoComplete="email"
                />
              </div>
              {errors.email && <span className="input-error-msg">⚠ {errors.email}</span>}
            </div>

// No verification code block
            {/* Password */}
            <div className="input-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="input-label" htmlFor="login-password">Password</label>
                <a href="#" style={{ fontSize: '0.78rem', color: 'var(--blue)', fontWeight: 500 }}>Forgot password?</a>
              </div>
              <div className="input-wrapper">
                <span className="input-icon"><IconLock /></span>
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  className={`input-field${errors.password ? ' error' : ''}`}
                  placeholder="Enter your password"
                  value={form.password}
                  onChange={update('password')}
                  autoComplete="current-password"
                  style={{ paddingRight: 44 }}
                />
                <button
                  type="button"
                  className="input-trailing-icon"
                  onClick={() => setShowPassword(s => !s)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <IconEyeOff /> : <IconEye />}
                </button>
              </div>
              {errors.password && <span className="input-error-msg">⚠ {errors.password}</span>}
            </div>

            {/* Submit */}
            <button
              type="submit"
              className="btn btn-primary btn-full btn-lg"
              disabled={loading}
              style={{ marginTop: 4 }}
            >
              {loading ? <span className="spinner" /> : null}
              {loading ? 'Signing in…' : 'Sign In'}
            </button>
          </form>

          <p className="auth-footer-text">
            Don&apos;t have an account?{' '}
            <Link to="/signup">Create one free</Link>
          </p>

          <p style={{ textAlign: 'center', fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 24 }}>
            🔒 End-to-end encrypted · Your data never leaves India
          </p>
        </div>
      </div>

      {/* Theme Toggle */}
      <button className="theme-toggle" onClick={toggle} aria-label="Toggle theme">
        {dark ? <IconSun /> : <IconMoon />}
      </button>
    </div>
  )
}
