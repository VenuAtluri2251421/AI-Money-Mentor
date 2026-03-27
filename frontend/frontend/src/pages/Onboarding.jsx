import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'
import StepForm from '../components/StepForm'
import { saveProfile } from '../api/client'

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

export default function Onboarding() {
  const navigate = useNavigate()
  const { dark, toggle } = useTheme()
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)

  const handleComplete = async (formData) => {
    setSubmitting(true)
    try {
      await saveProfile(formData)
    } catch {
      // save locally as fallback
      localStorage.setItem('artha_profile', JSON.stringify(formData))
    } finally {
      setSubmitting(false)
      setDone(true)
      setTimeout(() => navigate('/dashboard'), 1800)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-secondary)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 24px' }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 36, animation: 'fadeIn 0.4s ease both' }}>
        <div style={{ width: 56, height: 56, background: 'linear-gradient(135deg, var(--blue), var(--green))', borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.6rem', color: '#fff', fontWeight: 800, margin: '0 auto 16px' }}>₹</div>
        <h1 style={{ fontSize: '1.8rem', marginBottom: 8 }}>Set up your profile</h1>
        <p style={{ color: 'var(--text-secondary)', maxWidth: 420 }}>
          We need a few financial details to build your personalized plan. This takes about 2 minutes.
        </p>
      </div>

      {/* Card */}
      <div style={{ width: '100%', maxWidth: 520, background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 24, padding: '40px 36px', boxShadow: 'var(--shadow-lg)', animation: 'fadeIn 0.5s ease both' }}>
        {done ? (
          <div style={{ textAlign: 'center', padding: '40px 0', animation: 'fadeIn 0.4s ease both' }}>
            <div style={{ fontSize: '3.5rem', marginBottom: 16 }}>🎉</div>
            <h2 style={{ marginBottom: 10, color: 'var(--green)' }}>You're all set!</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Taking you to your dashboard…</p>
            <div style={{ width: 40, height: 4, background: 'var(--border)', borderRadius: 9999, margin: '24px auto 0', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: '100%', background: 'linear-gradient(90deg, var(--blue), var(--green))', animation: 'none', transform: 'translateX(-100%)', transition: 'transform 1.5s ease' }} />
            </div>
          </div>
        ) : (
          <StepForm onComplete={handleComplete} />
        )}
      </div>

      <p style={{ marginTop: 20, fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center' }}>
        🔒 Your data is encrypted and never shared with third parties
      </p>

      <button className="theme-toggle" onClick={toggle} aria-label="Toggle theme">
        {dark ? <IconSun /> : <IconMoon />}
      </button>
    </div>
  )
}
