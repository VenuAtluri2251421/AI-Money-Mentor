import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'

export default function TaxOptimizer() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    gross_income: '',
    age: '30',
    sec80c: '0',
    section_80d: '0',
    hra: '0',
    nps_80ccd: '0',
    home_loan_interest: '0',
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
      const { data } = await api.post('calculate/tax/compare', {
        gross_income: parseFloat(form.gross_income),
        age: parseInt(form.age),
        deductions: {
          sec80c: parseFloat(form.sec80c) || 0,
          section_80d: parseFloat(form.section_80d) || 0,
          hra: parseFloat(form.hra) || 0,
          nps_80ccd: parseFloat(form.nps_80ccd) || 0,
          home_loan_interest: parseFloat(form.home_loan_interest) || 0,
        },
      })
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Calculation failed.')
    } finally {
      setLoading(false)
    }
  }

  const fmt = (n) => `₹${Math.round(n || 0).toLocaleString('en-IN')}`

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-secondary)' }}>
      <nav style={{ background: 'var(--bg-card)', borderBottom: '1px solid var(--border)', padding: '0 24px', height: 60, display: 'flex', alignItems: 'center', gap: 12 }}>
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/dashboard')}>← Dashboard</button>
        <span style={{ fontWeight: 700 }}>🧾 Tax Optimizer</span>
      </nav>

      <div className="container" style={{ padding: '32px 24px', maxWidth: 800 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: '3rem', marginBottom: 8 }}>🧾</div>
          <h1 style={{ marginBottom: 8 }}>Tax Optimizer</h1>
          <p style={{ color: 'var(--text-secondary)', maxWidth: 500, margin: '0 auto' }}>
            Compare Old vs New regime and find the best tax-saving strategy for FY 2025-26.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="card" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          <div className="input-group" style={{ gridColumn: '1 / -1' }}>
            <label className="input-label">Gross Annual Income (₹) *</label>
            <input className="input-field input-no-icon" name="gross_income" type="number" placeholder="e.g. 1500000" value={form.gross_income} onChange={handleChange} required />
          </div>
          <div className="input-group">
            <label className="input-label">Age</label>
            <input className="input-field input-no-icon" name="age" type="number" value={form.age} onChange={handleChange} />
          </div>
          <div className="input-group">
            <label className="input-label">Section 80C (₹)</label>
            <input className="input-field input-no-icon" name="sec80c" type="number" placeholder="PPF, ELSS, LIC etc." value={form.sec80c} onChange={handleChange} />
          </div>
          <div className="input-group">
            <label className="input-label">Section 80D (₹)</label>
            <input className="input-field input-no-icon" name="section_80d" type="number" placeholder="Medical Insurance" value={form.section_80d} onChange={handleChange} />
          </div>
          <div className="input-group">
            <label className="input-label">HRA Exemption (₹)</label>
            <input className="input-field input-no-icon" name="hra" type="number" placeholder="House Rent Allowance" value={form.hra} onChange={handleChange} />
          </div>
          <div className="input-group">
            <label className="input-label">NPS 80CCD(1B) (₹)</label>
            <input className="input-field input-no-icon" name="nps_80ccd" type="number" placeholder="Up to ₹50,000" value={form.nps_80ccd} onChange={handleChange} />
          </div>
          <div className="input-group">
            <label className="input-label">Home Loan Interest (₹)</label>
            <input className="input-field input-no-icon" name="home_loan_interest" type="number" placeholder="Section 24(b)" value={form.home_loan_interest} onChange={handleChange} />
          </div>
          <div style={{ gridColumn: '1 / -1' }}>
            <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading}>
              {loading ? <span className="spinner" /> : '🧾 Compare Tax Regimes'}
            </button>
          </div>
          {error && <p style={{ gridColumn: '1 / -1', color: '#EF4444', textAlign: 'center' }}>{error}</p>}
        </form>

        {result && (
          <div className="animate-fade-in" style={{ marginTop: 24 }}>
            {/* Recommended badge */}
            <div style={{ textAlign: 'center', marginBottom: 16 }}>
              <span className={`badge ${result.recommended === 'new' ? 'badge-green' : 'badge-blue'}`} style={{ fontSize: '0.85rem', padding: '6px 16px' }}>
                ✅ {result.recommended === 'new' ? 'New' : 'Old'} Regime saves you {fmt(result.savings)}
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              {/* Old Regime */}
              <div className="card" style={{ borderTop: '4px solid var(--blue)' }}>
                <h3 style={{ marginBottom: 16, color: 'var(--blue)' }}>Old Regime</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <TaxRow label="Gross Income" value={fmt(result.old_regime?.gross_income)} />
                  <TaxRow label="Total Deductions" value={fmt(result.old_regime?.total_deductions)} />
                  <TaxRow label="Taxable Income" value={fmt(result.old_regime?.taxable_income)} />
                  <TaxRow label="Tax Before Cess" value={fmt(result.old_regime?.tax_before_cess)} />
                  <TaxRow label="Cess (4%)" value={fmt(result.old_regime?.cess)} />
                  <div style={{ borderTop: '2px solid var(--border)', paddingTop: 12, marginTop: 4 }}>
                    <TaxRow label="Total Tax" value={fmt(result.old_regime?.total_tax)} highlight />
                  </div>
                </div>
              </div>

              {/* New Regime */}
              <div className="card" style={{ borderTop: '4px solid var(--green)' }}>
                <h3 style={{ marginBottom: 16, color: 'var(--green)' }}>New Regime</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <TaxRow label="Gross Income" value={fmt(result.new_regime?.gross_income)} />
                  <TaxRow label="Std Deduction" value={fmt(result.new_regime?.total_deductions)} />
                  <TaxRow label="Taxable Income" value={fmt(result.new_regime?.taxable_income)} />
                  <TaxRow label="Tax Before Cess" value={fmt(result.new_regime?.tax_before_cess)} />
                  <TaxRow label="Cess (4%)" value={fmt(result.new_regime?.cess)} />
                  <div style={{ borderTop: '2px solid var(--border)', paddingTop: 12, marginTop: 4 }}>
                    <TaxRow label="Total Tax" value={fmt(result.new_regime?.total_tax)} highlight />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function TaxRow({ label, value, highlight }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ fontSize: '0.85rem', color: highlight ? 'var(--text-primary)' : 'var(--text-secondary)', fontWeight: highlight ? 700 : 400 }}>{label}</span>
      <span style={{ fontWeight: 700, fontSize: highlight ? '1.1rem' : '0.9rem', color: highlight ? 'var(--blue)' : 'var(--text-primary)' }}>{value}</span>
    </div>
  )
}
