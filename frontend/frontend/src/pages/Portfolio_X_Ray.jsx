import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'

export default function PortfolioXRay() {
  const navigate = useNavigate()
  const [rows, setRows] = useState([
    { date: '', amount: '' },
    { date: '', amount: '' },
  ])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const addRow = () => setRows([...rows, { date: '', amount: '' }])
  const removeRow = (i) => { if (rows.length > 2) setRows(rows.filter((_, idx) => idx !== i)) }

  const handleChange = (i, field, value) => {
    const updated = [...rows]
    updated[i][field] = value
    setRows(updated)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const cashflows = rows
        .filter(r => r.date && r.amount)
        .map(r => ({ date: r.date, amount: parseFloat(r.amount) }))
      if (cashflows.length < 2) { setError('Need at least 2 cashflows'); setLoading(false); return }
      const { data } = await api.post('calculate/xirr', { cashflows })
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'XIRR calculation failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-secondary)' }}>
      <nav style={{ background: 'var(--bg-card)', borderBottom: '1px solid var(--border)', padding: '0 24px', height: 60, display: 'flex', alignItems: 'center', gap: 12 }}>
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/dashboard')}>← Dashboard</button>
        <span style={{ fontWeight: 700 }}>🔬 Portfolio X-Ray</span>
      </nav>

      <div className="container" style={{ padding: '32px 24px', maxWidth: 800 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: '3rem', marginBottom: 8 }}>🔬</div>
          <h1 style={{ marginBottom: 8 }}>Portfolio X-Ray</h1>
          <p style={{ color: 'var(--text-secondary)', maxWidth: 500, margin: '0 auto' }}>
            Calculate XIRR — your true annualized return from a series of investments and redemptions.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="card">
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 16 }}>
            Enter your cashflows: <strong>negative</strong> amounts for investments (outflows), <strong>positive</strong> for redemptions (inflows). The last row should be today's portfolio value as a positive number.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {rows.map((row, i) => (
              <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 10, alignItems: 'center' }}>
                <input className="input-field input-no-icon" type="date" value={row.date} onChange={(e) => handleChange(i, 'date', e.target.value)} required style={{ height: 44 }} />
                <input className="input-field input-no-icon" type="number" placeholder={i === rows.length - 1 ? 'e.g. 150000 (current value)' : 'e.g. -10000 (invested)'} value={row.amount} onChange={(e) => handleChange(i, 'amount', e.target.value)} required style={{ height: 44 }} />
                {rows.length > 2 && (
                  <button type="button" onClick={() => removeRow(i)} className="btn btn-ghost btn-sm" style={{ width: 36, padding: 0, color: '#EF4444' }}>✕</button>
                )}
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
            <button type="button" onClick={addRow} className="btn btn-outline btn-sm">+ Add Row</button>
          </div>

          <div style={{ marginTop: 20 }}>
            <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading}>
              {loading ? <span className="spinner" /> : '🔬 Calculate XIRR'}
            </button>
          </div>
          {error && <p style={{ color: '#EF4444', textAlign: 'center', marginTop: 12 }}>{error}</p>}
        </form>

        {result && (
          <div className="card animate-fade-in" style={{ marginTop: 24, textAlign: 'center' }}>
            <h2 style={{ marginBottom: 20 }}>XIRR Result</h2>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
              <div style={{ padding: 20, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', borderLeft: '4px solid var(--blue)' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>XIRR</div>
                <div style={{ fontSize: '2rem', fontWeight: 800, color: (result.xirr_pct || 0) >= 0 ? 'var(--green)' : '#EF4444' }}>
                  {(result.xirr_pct || result.xirr * 100 || 0).toFixed(2)}%
                </div>
              </div>
              <div style={{ padding: 20, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', borderLeft: '4px solid var(--green)' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>Total Invested</div>
                <div style={{ fontSize: '1.3rem', fontWeight: 700 }}>₹{Math.abs(result.total_invested || 0).toLocaleString('en-IN')}</div>
              </div>
              <div style={{ padding: 20, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', borderLeft: '4px solid var(--blue-light)' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>Current Value</div>
                <div style={{ fontSize: '1.3rem', fontWeight: 700 }}>₹{(result.current_value || 0).toLocaleString('en-IN')}</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
