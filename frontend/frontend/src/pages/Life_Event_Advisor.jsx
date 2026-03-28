import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { advisorChat } from '../api/client'

const LIFE_EVENTS = [
  { id: 'bonus', icon: '💰', title: 'Got a Bonus', prompt: 'I just received a bonus of ₹{amount}. I am {age} years old with monthly income ₹{income}. How should I allocate this bonus between investments, emergency fund, and debt repayment?' },
  { id: 'marriage', icon: '💍', title: 'Getting Married', prompt: 'I am planning to get married soon. I am {age} years old with monthly income ₹{income} and savings of ₹{amount}. What financial preparations should I make? How should I budget for the wedding and plan finances as a couple?' },
  { id: 'baby', icon: '👶', title: 'Having a Baby', prompt: 'We are expecting a baby. I am {age} years old with monthly income ₹{income}. How should I prepare financially — insurance, savings, education fund? What changes to make in my investment strategy?' },
  { id: 'job_change', icon: '🚀', title: 'Job Change', prompt: 'I am switching jobs. My new salary is ₹{amount} per month (from ₹{income}). I am {age} years old. How should I handle the salary hike — increase SIP, prepay loans, or build emergency fund?' },
  { id: 'inheritance', icon: '🏛️', title: 'Received Inheritance', prompt: 'I received an inheritance of ₹{amount}. I am {age} years old with monthly income ₹{income}. How should I invest this lump sum? Should I pay off loans first or invest?' },
  { id: 'home', icon: '🏠', title: 'Buying a Home', prompt: 'I want to buy a home worth ₹{amount}. I am {age} years old with monthly income ₹{income}. How much down payment should I save? What EMI can I afford? Should I buy now or wait?' },
]

export default function LifeEventAdvisor() {
  const navigate = useNavigate()
  const [selected, setSelected] = useState(null)
  const [form, setForm] = useState({ age: '28', income: '80000', amount: '' })
  const [response, setResponse] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!selected) return
    setResponse('')
    setLoading(true)
    try {
      const event = LIFE_EVENTS.find(ev => ev.id === selected)
      const message = event.prompt
        .replace('{age}', form.age)
        .replace('{income}', form.income)
        .replace('{amount}', form.amount || 'not specified')
      const { data } = await advisorChat({ message })
      setResponse(data.response)
    } catch {
      setResponse('Sorry, I could not process your request right now. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-secondary)' }}>
      <nav style={{ background: 'var(--bg-card)', borderBottom: '1px solid var(--border)', padding: '0 24px', height: 60, display: 'flex', alignItems: 'center', gap: 12 }}>
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/dashboard')}>← Dashboard</button>
        <span style={{ fontWeight: 700 }}>🎯 Life Event Advisor</span>
      </nav>

      <div className="container" style={{ padding: '32px 24px', maxWidth: 800 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: '3rem', marginBottom: 8 }}>🎯</div>
          <h1 style={{ marginBottom: 8 }}>Life Event Advisor</h1>
          <p style={{ color: 'var(--text-secondary)', maxWidth: 500, margin: '0 auto' }}>
            Major life change? Dinero gives you a personalized financial action plan.
          </p>
        </div>

        {/* Event Selection */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 24 }}>
          {LIFE_EVENTS.map(ev => (
            <button key={ev.id} onClick={() => setSelected(ev.id)} className="card" style={{
              cursor: 'pointer', textAlign: 'center', padding: 20,
              border: selected === ev.id ? '2px solid var(--blue)' : '1px solid var(--border)',
              background: selected === ev.id ? 'var(--blue-bg)' : 'var(--bg-card)',
              transform: 'none',
            }}>
              <div style={{ fontSize: '2rem', marginBottom: 8 }}>{ev.icon}</div>
              <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{ev.title}</div>
            </button>
          ))}
        </div>

        {/* Input Form */}
        {selected && (
          <form onSubmit={handleSubmit} className="card animate-fade-in" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
            <div className="input-group">
              <label className="input-label">Your Age</label>
              <input className="input-field input-no-icon" type="number" value={form.age} onChange={e => setForm({ ...form, age: e.target.value })} />
            </div>
            <div className="input-group">
              <label className="input-label">Monthly Income (₹)</label>
              <input className="input-field input-no-icon" type="number" value={form.income} onChange={e => setForm({ ...form, income: e.target.value })} />
            </div>
            <div className="input-group">
              <label className="input-label">Amount (₹)</label>
              <input className="input-field input-no-icon" type="number" placeholder="Bonus / Home price etc." value={form.amount} onChange={e => setForm({ ...form, amount: e.target.value })} />
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading}>
                {loading ? <span className="spinner" /> : `🎯 Get Advice for "${LIFE_EVENTS.find(e => e.id === selected)?.title}"`}
              </button>
            </div>
          </form>
        )}

        {/* AI Response */}
        {response && (
          <div className="card animate-fade-in" style={{ marginTop: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <div style={{ width: 32, height: 32, background: 'linear-gradient(135deg, var(--blue), var(--green))', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.9rem' }}>🤖</div>
              <h3>Dinero's Advice</h3>
            </div>
            <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.7, color: 'var(--text-secondary)', fontSize: '0.92rem' }}>
              {response}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
