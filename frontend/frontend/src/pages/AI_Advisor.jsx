import { useNavigate } from 'react-router-dom'
import AIChat from '../components/AIChat'
import { useTheme } from '../context/ThemeContext'

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

export default function AIAdvisor() {
  const navigate = useNavigate()
  const { dark, toggle } = useTheme()
  const profile = JSON.parse(localStorage.getItem('artha_profile') || '{}')

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-secondary)' }}>
      <nav style={{ background: 'var(--bg-card)', borderBottom: '1px solid var(--border)', padding: '0 24px', height: 60, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/dashboard')}>← Dashboard</button>
          <span style={{ fontWeight: 700 }}>🤖 AI Financial Advisor</span>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={toggle} aria-label="Toggle theme">
          {dark ? <IconSun /> : <IconMoon />}
        </button>
      </nav>
      <div className="container" style={{ padding: '40px 24px', maxWidth: 720 }}>
        <div style={{ marginBottom: 24, animation: 'fadeIn 0.4s ease both' }}>
          <h1 style={{ marginBottom: 8 }}>AI Financial Advisor</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Conversational mentor powered by Claude — asks questions using your real financial data as context.
          </p>
        </div>
        <div style={{ animation: 'fadeIn 0.5s 0.1s ease both' }}>
          <AIChat profile={profile} />
        </div>
      </div>
    </div>
  )
}
