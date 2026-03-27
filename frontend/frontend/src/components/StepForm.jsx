import { useState } from 'react'

const STEP_LABELS = ['Personal', 'Income', 'Expenses', 'Savings']

const steps = [
  {
    title: 'Tell us about yourself',
    subtitle: 'A little background helps us personalize your plan.',
    fields: [
      { key: 'age',        label: 'Your Age',                type: 'number', placeholder: '28',           min: 18, max: 80, unit: 'years' },
      { key: 'retireAge',  label: 'Target Retirement Age',   type: 'number', placeholder: '50',           min: 30, max: 80, unit: 'years' },
    ],
  },
  {
    title: 'Income details',
    subtitle: 'Enter your annual take-home income after taxes.',
    fields: [
      { key: 'income',     label: 'Annual Income',           type: 'number', placeholder: '12,00,000',    unit: '₹', prefix: true },
      { key: 'otherIncome',label: 'Other Income (optional)', type: 'number', placeholder: '0',            unit: '₹', prefix: true },
    ],
  },
  {
    title: 'Monthly expenses',
    subtitle: 'Total money you spend every month.',
    fields: [
      { key: 'expenses',   label: 'Monthly Expenses',        type: 'number', placeholder: '40,000',       unit: '₹', prefix: true },
      { key: 'emi',        label: 'EMI / Loan payments',     type: 'number', placeholder: '0',            unit: '₹', prefix: true },
    ],
  },
  {
    title: 'Current savings',
    subtitle: 'What you have saved and invested so far.',
    fields: [
      { key: 'savings',    label: 'Savings & Investments',   type: 'number', placeholder: '5,00,000',     unit: '₹', prefix: true },
      { key: 'epf',        label: 'EPF / PPF balance',       type: 'number', placeholder: '0',            unit: '₹', prefix: true },
    ],
  },
]

export default function StepForm({ onComplete }) {
  const [step, setStep] = useState(0)
  const [data, setData] = useState({})
  const [direction, setDirection] = useState('forward')
  const [errors, setErrors] = useState({})

  const current = steps[step]
  const isLast  = step === steps.length - 1

  const update = (key) => (e) => {
    setData(d => ({ ...d, [key]: e.target.value }))
    if (errors[key]) setErrors(er => ({ ...er, [key]: '' }))
  }

  const validate = () => {
    const errs = {}
    current.fields.forEach(({ key, label, min, max, type }) => {
      const val = data[key]
      if (key === 'otherIncome' || key === 'emi' || key === 'epf') return // optional
      if (!val && val !== 0) { errs[key] = `${label} is required`; return }
      if (type === 'number') {
        const n = Number(val)
        if (isNaN(n)) { errs[key] = 'Enter a valid number'; return }
        if (min !== undefined && n < min) errs[key] = `Minimum is ${min}`
        if (max !== undefined && n > max) errs[key] = `Maximum is ${max}`
      }
    })
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const goNext = () => {
    if (!validate()) return
    if (isLast) { onComplete && onComplete(data); return }
    setDirection('forward')
    setStep(s => s + 1)
  }

  const goBack = () => {
    setDirection('back')
    setStep(s => s - 1)
  }

  return (
    <div>
      {/* ── Progress ────────────────────────────────────────── */}
      <div style={{ marginBottom: 32 }}>
        {/* Bar */}
        <div style={{ height: 4, background: 'var(--border)', borderRadius: 9999, marginBottom: 16, overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${((step + 1) / steps.length) * 100}%`, background: 'linear-gradient(90deg, var(--blue), var(--green))', borderRadius: 9999, transition: 'width 0.4s cubic-bezier(0.4,0,0.2,1)' }} />
        </div>
        {/* Step dots */}
        <div style={{ display: 'flex', gap: 8 }}>
          {STEP_LABELS.map((label, i) => (
            <div key={label} style={{ flex: 1, textAlign: 'center' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                <div style={{ width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, transition: 'all 0.3s', background: i < step ? 'var(--green)' : i === step ? 'var(--blue)' : 'var(--border)', color: i <= step ? '#fff' : 'var(--text-muted)' }}>
                  {i < step ? '✓' : i + 1}
                </div>
                <span style={{ fontSize: '0.65rem', color: i === step ? 'var(--blue)' : 'var(--text-muted)', fontWeight: i === step ? 600 : 400, display: window.innerWidth > 480 ? 'block' : 'none' }}>{label}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Step Content ───────────────────────────────────── */}
      <div key={step} style={{ animation: `${direction === 'forward' ? 'slideLeft' : 'slideRight'} 0.3s ease both` }}>
        <h2 style={{ fontSize: '1.4rem', marginBottom: 6 }}>{current.title}</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: 28, fontSize: '0.9rem' }}>{current.subtitle}</p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          {current.fields.map(({ key, label, type, placeholder, unit, prefix }) => (
            <div className="input-group" key={key}>
              <label className="input-label" htmlFor={`sf-${key}`}>{label}</label>
              <div className="input-wrapper">
                {prefix && (
                  <span className="input-icon" style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{unit}</span>
                )}
                <input
                  id={`sf-${key}`}
                  type={type}
                  className={`input-field${!prefix ? ' input-no-icon' : ''}${errors[key] ? ' error' : ''}`}
                  placeholder={placeholder}
                  value={data[key] || ''}
                  onChange={update(key)}
                  min={0}
                  style={!prefix ? { paddingLeft: 16 } : {}}
                />
                {!prefix && unit && (
                  <span style={{ position: 'absolute', right: 14, color: 'var(--text-muted)', fontSize: '0.85rem' }}>{unit}</span>
                )}
              </div>
              {errors[key] && <span className="input-error-msg">⚠ {errors[key]}</span>}
            </div>
          ))}
        </div>
      </div>

      {/* ── Navigation ─────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 12, marginTop: 36 }}>
        {step > 0 && (
          <button className="btn btn-ghost" style={{ flex: 1, border: '1.5px solid var(--border)' }} onClick={goBack}>
            ← Back
          </button>
        )}
        <button className="btn btn-primary" style={{ flex: 2 }} onClick={goNext}>
          {isLast ? '🚀 Complete Setup' : 'Continue →'}
        </button>
      </div>

      <p style={{ textAlign: 'center', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 16 }}>
        Step {step + 1} of {steps.length}
      </p>
    </div>
  )
}
