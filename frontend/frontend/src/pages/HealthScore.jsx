import { useNavigate } from 'react-router-dom'
export default function HealthScore() {
  const navigate = useNavigate()
  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-secondary)' }}>
      <nav style={{ background: 'var(--bg-card)', borderBottom: '1px solid var(--border)', padding: '0 24px', height: 60, display: 'flex', alignItems: 'center', gap: 12 }}>
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/dashboard')}>← Dashboard</button>
        <span style={{ fontWeight: 700 }}>💚 Health Score Detail</span>
      </nav>
      <div className="container" style={{ padding: '48px 24px', textAlign: 'center' }}>
        <div style={{ fontSize: '4rem', marginBottom: 16 }}>💚</div>
        <h1 style={{ marginBottom: 12 }}>Detailed Health Score</h1>
        <p style={{ color: 'var(--text-secondary)', maxWidth: 480, margin: '0 auto 32px' }}>
          Deep-dive into your financial health breakdown with actionable recommendations for each dimension.
        </p>
        <div className="badge badge-green">Coming in Phase 6</div>
      </div>
    </div>
  )
}
