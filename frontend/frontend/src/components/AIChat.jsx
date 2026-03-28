import { useState, useRef, useEffect } from 'react'
import { advisorChat } from '../api/client'

const IconSend = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
    <line x1="22" y1="2" x2="11" y2="13"/>
    <polygon points="22 2 15 22 11 13 2 9 22 2"/>
  </svg>
)

const IconBot = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
    <rect x="3" y="11" width="18" height="10" rx="2"/>
    <circle cx="12" cy="5" r="2"/>
    <path d="M12 7v4"/>
    <line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/>
  </svg>
)

const STARTERS = [
  'How much should I invest monthly to retire by 50?',
  'What tax deductions am I missing?',
  'Is my emergency fund sufficient?',
  'How diversified is my portfolio?',
]

export default function AIChat({ profile }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Hello! I\'m your Dinero advisor. Ask me anything about your finances — I\'ll use your actual data to give you personalized answers. 🙏' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (text) => {
    const q = (text || input).trim()
    if (!q) return
    setInput('')
    setMessages(m => [...m, { role: 'user', text: q }])
    setLoading(true)
    try {
      const token = localStorage.getItem('artha_token')
      // Note: adjust the URL if your backend runs on a different host/port
      const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
      const res = await fetch(`${API_BASE}/advisor/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ message: q, profile })
      })

      if (!res.ok) throw new Error('API error')

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let botReply = ''
      
      setMessages(m => [...m, { role: 'assistant', text: '' }])
      setLoading(false) // Stop pulsing once stream starts reading

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim()
            if (dataStr === '[DONE]' || !dataStr) continue
            try {
              const data = JSON.parse(dataStr)
              if (data.text) botReply += data.text
            } catch (e) {
              // Fallback if backend sends plain strings
              botReply += dataStr
            }
            
            setMessages(m => {
              const newM = [...m]
              newM[newM.length - 1] = { role: 'assistant', text: botReply }
              return newM
            })
          }
        }
      }
    } catch {
      setMessages(m => [...m, { role: 'assistant', text: '⚠️ Sorry, I couldn\'t connect to the advisor right now. Please try again.' }])
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 520, background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 20, overflow: 'hidden', boxShadow: 'var(--shadow-card)' }}>
      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 10, background: 'linear-gradient(135deg, var(--blue-bg), var(--green-bg))' }}>
        <div style={{ width: 36, height: 36, background: 'linear-gradient(135deg, var(--blue), var(--green))', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
          <IconBot />
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>Dinero Advisor</div>
          <div style={{ fontSize: '0.72rem', color: 'var(--green)', display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 6, height: 6, background: 'var(--green)', borderRadius: '50%', display: 'inline-block' }} />
            Online · Powered by Gemini
          </div>
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start', animation: 'fadeIn 0.3s ease both' }}>
            <div style={{ maxWidth: '80%', padding: '10px 14px', borderRadius: msg.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px', background: msg.role === 'user' ? 'var(--blue)' : 'var(--bg-secondary)', color: msg.role === 'user' ? '#fff' : 'var(--text-primary)', fontSize: '0.88rem', lineHeight: 1.6, border: msg.role !== 'user' ? '1px solid var(--border)' : 'none' }}>
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ display: 'flex', gap: 6, padding: '10px 14px', background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: '18px 18px 18px 4px', width: 'fit-content' }}>
            {[0, 0.2, 0.4].map((delay, i) => (
              <div key={i} style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--text-muted)', animation: `pulse 1.2s ${delay}s ease-in-out infinite` }} />
            ))}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Starters (shown when only 1 message) */}
      {messages.length === 1 && (
        <div style={{ padding: '0 20px 12px', display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {STARTERS.map(s => (
            <button key={s} onClick={() => send(s)} style={{ background: 'var(--blue-bg)', color: 'var(--blue)', border: '1px solid var(--blue-lighter)', borderRadius: 9999, padding: '4px 12px', fontSize: '0.75rem', fontWeight: 500, cursor: 'pointer', transition: 'all 0.2s', fontFamily: 'inherit' }}>
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div style={{ padding: '12px 20px', borderTop: '1px solid var(--border)', display: 'flex', gap: 10 }}>
        <input
          type="text"
          className="input-field input-no-icon"
          style={{ flex: 1, height: 44 }}
          placeholder="Ask anything about your finances…"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
          disabled={loading}
        />
        <button className="btn btn-primary" style={{ width: 44, height: 44, padding: 0 }} onClick={() => send()} disabled={loading || !input.trim()} aria-label="Send message">
          <IconSend />
        </button>
      </div>
    </div>
  )
}
