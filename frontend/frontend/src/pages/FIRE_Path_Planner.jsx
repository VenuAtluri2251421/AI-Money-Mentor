import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { calculateFire } from '../api/client'

export default function FIREPathPlanner() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    annual_expenses: '',
    inflation_pct: '6',
    expected_return_pct: '12',
    safe_withdrawal_rate: '4',
    current_corpus: '0',
    years_to_retirement: '',
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
      const payload = {
        annual_expenses: parseFloat(form.annual_expenses),
        inflation_pct: parseFloat(form.inflation_pct),
        expected_return_pct: parseFloat(form.expected_return_pct),
        safe_withdrawal_rate: parseFloat(form.safe_withdrawal_rate),
        current_corpus: parseFloat(form.current_corpus) || 0,
      }
      if (form.years_to_retirement) payload.years_to_retirement = parseFloat(form.years_to_retirement)
      const { data } = await calculateFire(payload)
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Calculation failed. Please check your inputs.')
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (n) => {
    if (n >= 10000000) return `₹${(n / 10000000).toFixed(2)} Cr`
    if (n >= 100000) return `₹${(n / 100000).toFixed(2)} L`
    return `₹${n?.toLocaleString('en-IN')}`
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-secondary)' }}>
      <nav style={{ background: 'var(--bg-card)', borderBottom: '1px solid var(--border)', padding: '0 24px', height: 60, display: 'flex', alignItems: 'center', gap: 12 }}>
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/dashboard')}>← Dashboard</button>
        <span style={{ fontWeight: 700 }}>🔥 FIRE Path Planner</span>
      </nav>

      <div className="container" style={{ padding: '32px 24px', maxWidth: 800 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: '3rem', marginBottom: 8 }}>🔥</div>
          <h1 style={{ marginBottom: 8 }}>FIRE Path Planner</h1>
          <p style={{ color: 'var(--text-secondary)', maxWidth: 500, margin: '0 auto' }}>
            Calculate your Financial Independence number and how long it takes to get there.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="card" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          <div className="input-group">
            <label className="input-label">Annual Expenses (₹) *</label>
            <input className="input-field input-no-icon" name="annual_expenses" type="number" placeholder="e.g. 600000" value={form.annual_expenses} onChange={handleChange} required />
          </div>
          <div className="input-group">
            <label className="input-label">Current Corpus (₹)</label>
            <input className="input-field input-no-icon" name="current_corpus" type="number" placeholder="e.g. 500000" value={form.current_corpus} onChange={handleChange} />
          </div>
          <div className="input-group">
            <label className="input-label">Inflation Rate (%)</label>
            <input className="input-field input-no-icon" name="inflation_pct" type="number" step="0.1" value={form.inflation_pct} onChange={handleChange} />
          </div>
          <div className="input-group">
            <label className="input-label">Expected Return (%)</label>
            <input className="input-field input-no-icon" name="expected_return_pct" type="number" step="0.1" value={form.expected_return_pct} onChange={handleChange} />
          </div>
          <div className="input-group">
            <label className="input-label">Safe Withdrawal Rate (%)</label>
            <input className="input-field input-no-icon" name="safe_withdrawal_rate" type="number" step="0.1" value={form.safe_withdrawal_rate} onChange={handleChange} />
          </div>
          <div className="input-group">
            <label className="input-label">Years to Retirement (optional)</label>
            <input className="input-field input-no-icon" name="years_to_retirement" type="number" placeholder="e.g. 25" value={form.years_to_retirement} onChange={handleChange} />
          </div>
          <div style={{ gridColumn: '1 / -1' }}>
            <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading}>
              {loading ? <span className="spinner" /> : '🔥 Calculate FIRE Number'}
            </button>
          </div>
          {error && <p style={{ gridColumn: '1 / -1', color: '#EF4444', textAlign: 'center' }}>{error}</p>}
        </form>

        {result && (
          <div className="card animate-fade-in" style={{ marginTop: 24 }}>
            <h2 style={{ marginBottom: 20, textAlign: 'center' }}>Your FIRE Results</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
              <ResultCard label="FIRE Number" value={formatCurrency(result.fire_number)} color="var(--blue)" />
              <ResultCard label="Monthly SIP Needed" value={formatCurrency(result.required_monthly_sip || 0)} color="var(--green)" />
              <ResultCard label="Future Annual Expenses" value={formatCurrency(result.future_annual_expenses || result.fire_number * (parseFloat(form.safe_withdrawal_rate) / 100))} color="var(--blue-light)" />
              {result.years_to_fire && <ResultCard label="Years to FIRE" value={`${result.years_to_fire} years`} color="var(--green)" />}
            </div>
            {result.monthly_projection && result.monthly_projection.length > 0 && (
              <div style={{ marginTop: 20, padding: 16, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)' }}>
                <h4 style={{ marginBottom: 8 }}>📈 Growth Projection</h4>
                <div style={{ display: 'flex', gap: 12, overflowX: 'auto', paddingBottom: 8 }}>
                  {result.monthly_projection.filter((_, i) => i % 12 === 0).slice(0, 10).map((val, i) => (
                    <div key={i} style={{ textAlign: 'center', minWidth: 80 }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Year {i + 1}</div>
                      <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>{formatCurrency(val)}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function ResultCard({ label, value, color }) {
  return (
    <div style={{ padding: 20, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', textAlign: 'center', borderLeft: `4px solid ${color}` }}>
      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
      <div style={{ fontSize: '1.4rem', fontWeight: 800, color }}>{value}</div>
    </div>
  )
}
