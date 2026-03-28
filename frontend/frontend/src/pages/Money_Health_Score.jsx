import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { calculateHealth } from '../api/client'

export default function MoneyHealthScore() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    monthly_income: '', monthly_expenses: '', emergency_fund: '0',
    total_emi: '0', credit_card_balance: '0',
    equity_investments: '0', debt_investments: '0', gold_investments: '0',
    life_cover: '0', health_cover: '0',
    age: '30', monthly_sip: '0', current_corpus: '0',
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const payload = {}
      Object.keys(form).forEach(k => { payload[k] = parseFloat(form[k]) || 0 })
      payload.monthly_income = parseFloat(form.monthly_income)
      payload.monthly_expenses = parseFloat(form.monthly_expenses)
      payload.monthly_fixed_expenses = parseFloat(form.monthly_expenses)
      const { data } = await calculateHealth(payload)
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Calculation failed.')
    } finally {
      setLoading(false)
    }
  }

  const gradeColor = (grade) => {
    if (grade === 'Excellent' || grade === 'Good') return 'var(--green)'
    if (grade === 'Fair') return '#F59E0B'
    return '#EF4444'
  }

  const scoreBarColor = (pct) => {
    if (pct >= 80) return 'var(--green)'
    if (pct >= 50) return '#F59E0B'
    return '#EF4444'
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-secondary)' }}>
      <nav style={{ background: 'var(--bg-card)', borderBottom: '1px solid var(--border)', padding: '0 24px', height: 60, display: 'flex', alignItems: 'center', gap: 12 }}>
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/dashboard')}>← Dashboard</button>
        <span style={{ fontWeight: 700 }}>🩺 Money Health Score</span>
      </nav>

      <div className="container" style={{ padding: '32px 24px', maxWidth: 800 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: '3rem', marginBottom: 8 }}>🩺</div>
          <h1 style={{ marginBottom: 8 }}>Money Health Score</h1>
          <p style={{ color: 'var(--text-secondary)', maxWidth: 500, margin: '0 auto' }}>
            Score your financial wellness across 6 dimensions.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="card" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          <div className="input-group">
            <label className="input-label">Monthly Income (₹) *</label>
            <input className="input-field input-no-icon" name="monthly_income" type="number" placeholder="e.g. 80000" value={form.monthly_income} onChange={handleChange} required />
          </div>
          <div className="input-group">
            <label className="input-label">Monthly Expenses (₹) *</label>
            <input className="input-field input-no-icon" name="monthly_expenses" type="number" placeholder="e.g. 40000" value={form.monthly_expenses} onChange={handleChange} required />
          </div>
          <div className="input-group">
            <label className="input-label">Emergency Fund (₹)</label>
            <input className="input-field input-no-icon" name="emergency_fund" type="number" value={form.emergency_fund} onChange={handleChange} />
          </div>
          <div className="input-group">
            <label className="input-label">Total EMI (₹/month)</label>
            <input className="input-field input-no-icon" name="total_emi" type="number" value={form.total_emi} onChange={handleChange} />
          </div>
          <div className="input-group">
            <label className="input-label">Equity Investments (₹)</label>
            <input className="input-field input-no-icon" name="equity_investments" type="number" value={form.equity_investments} onChange={handleChange} />
          </div>
          <div className="input-group">
            <label className="input-label">Debt Investments (₹)</label>
            <input className="input-field input-no-icon" name="debt_investments" type="number" value={form.debt_investments} onChange={handleChange} />
          </div>
          <div className="input-group">
            <label className="input-label">Life Cover (₹)</label>
            <input className="input-field input-no-icon" name="life_cover" type="number" value={form.life_cover} onChange={handleChange} />
          </div>
          <div className="input-group">
            <label className="input-label">Health Cover (₹)</label>
            <input className="input-field input-no-icon" name="health_cover" type="number" value={form.health_cover} onChange={handleChange} />
          </div>
          <div className="input-group">
            <label className="input-label">Age</label>
            <input className="input-field input-no-icon" name="age" type="number" value={form.age} onChange={handleChange} />
          </div>
          <div className="input-group">
            <label className="input-label">Monthly SIP (₹)</label>
            <input className="input-field input-no-icon" name="monthly_sip" type="number" value={form.monthly_sip} onChange={handleChange} />
          </div>
          <div style={{ gridColumn: '1 / -1' }}>
            <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading}>
              {loading ? <span className="spinner" /> : '🩺 Check Health Score'}
            </button>
          </div>
          {error && <p style={{ gridColumn: '1 / -1', color: '#EF4444', textAlign: 'center' }}>{error}</p>}
        </form>

        {result && (
          <div className="card animate-fade-in" style={{ marginTop: 24 }}>
            {/* Overall Score */}
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <div style={{ fontSize: '4rem', fontWeight: 800, color: gradeColor(result.grade) }}>{result.overall_score}</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: gradeColor(result.grade) }}>{result.grade}</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>out of 100</div>
            </div>

            {/* Dimension Bars */}
            <h3 style={{ marginBottom: 16 }}>Score Breakdown</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {result.dimensions?.map((dim) => (
                <div key={dim.name}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{dim.name}</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{dim.score}/{dim.max_score} ({dim.pct}%)</span>
                  </div>
                  <div style={{ height: 10, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-pill)', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${dim.pct}%`, background: scoreBarColor(dim.pct), borderRadius: 'var(--radius-pill)', transition: 'width 0.8s ease' }} />
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 2 }}>{dim.insight}</div>
                </div>
              ))}
            </div>

            {/* Action Items */}
            {result.action_items?.length > 0 && (
              <div style={{ marginTop: 24, padding: 16, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)' }}>
                <h4 style={{ marginBottom: 8 }}>💡 Action Items</h4>
                <ul style={{ paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {result.action_items.map((item, i) => (
                    <li key={i} style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
