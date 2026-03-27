import { useNavigate } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'
import { useState, useEffect, useRef } from 'react'
import { getProfile, getPortfolios } from '../api/client'
import './Dashboard.css'

/* ── SVG Icons ─────────────────────────────────────────── */
const IconLogout = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
    <polyline points="16 17 21 12 16 7"/>
    <line x1="21" y1="12" x2="9" y2="12"/>
  </svg>
)
const IconArrow = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16">
    <line x1="5" y1="12" x2="19" y2="12"/>
    <polyline points="12 5 19 12 12 19"/>
  </svg>
)

const FEATURES = [
  { id: 'fire',           emoji: '🔥', title: 'FIRE Path Planner',    desc: 'Simulate wealth growth using compound interest & project your retirement timeline.',               color: '#F97316', border: 'rgba(249,115,22,0.25)', route: '/fire'           },
  { id: 'health-score',   emoji: '🩺', title: 'Money Health Score',   desc: 'Score your financial wellness across 6 deep dimensions — emergency fund, insurance & more.',       color: '#4ADE80', border: 'rgba(74,222,128,0.25)', route: '/health-score'   },
  { id: 'life-events',    emoji: '🎯', title: 'Life Event Advisor',   desc: 'Smart allocation guidance for bonuses, inheritance & big life changes.',                          color: '#A78BFA', border: 'rgba(167,139,250,0.25)', route: '/life-events'   },
  { id: 'tax',            emoji: '🧾', title: 'Tax Optimizer',        desc: 'Old vs new regime comparison — find 80C/80D gaps & save up to ₹1.5L/year.',                       color: '#FBBF24', border: 'rgba(251,191,36,0.25)', route: '/tax'            },
  { id: 'portfolio-xray', emoji: '🔬', title: 'Portfolio X-Ray',      desc: 'XIRR analysis, fund overlap detection, expense ratios & smart rebalancing ideas.',                color: '#22D3EE', border: 'rgba(34,211,238,0.25)', route: '/portfolio-xray' },
  { id: 'ai-advisor',     emoji: '🤖', title: 'AI Financial Advisor', desc: 'Conversational mentor powered by Gemini — your data, your questions, real-time streaming answers.', color: '#3B82F6', border: 'rgba(59,130,246,0.25)', route: '/ai-advisor'     },
]

/* ── Constellation Canvas (same engine as Landing) ─────── */
function ConstellationBg() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    let animId
    const particles = []
    const PARTICLE_COUNT = 60

    const resize = () => { canvas.width = canvas.offsetWidth; canvas.height = canvas.offsetHeight }
    resize()
    window.addEventListener('resize', resize)

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        r: Math.random() * 1.5 + 0.5,
      })
    }

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      particles.forEach((p) => {
        p.x += p.vx; p.y += p.vy
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
        ctx.fillStyle = 'rgba(59,130,246,0.5)'
        ctx.fill()
      })
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x
          const dy = particles[i].y - particles[j].y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < 120) {
            ctx.beginPath()
            ctx.moveTo(particles[i].x, particles[i].y)
            ctx.lineTo(particles[j].x, particles[j].y)
            ctx.strokeStyle = `rgba(59,130,246,${0.08 * (1 - dist / 120)})`
            ctx.stroke()
          }
        }
      }
      animId = requestAnimationFrame(draw)
    }
    draw()
    return () => { cancelAnimationFrame(animId); window.removeEventListener('resize', resize) }
  }, [])

  return <canvas ref={canvasRef} className="dash-constellation" />
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { dark, toggle } = useTheme()

  const [stats, setStats] = useState({ fire: '...', health: '74/100', tax: '...', port: '...' })

  useEffect(() => {
    getProfile()
      .then(res => {
        const p = res.data
        localStorage.setItem('artha_profile', JSON.stringify(p))
        setStats(s => ({ ...s, fire: p.retirement_age ? `Age ${p.retirement_age}` : 'TBD', tax: p.tax_regime || 'Unknown' }))
      })
      .catch((err) => {
        if (err.response?.status === 404) {
          setStats(s => ({ ...s, fire: 'Setup needed', tax: 'Setup needed' }))
        } else {
          setStats(s => ({ ...s, fire: 'Error', tax: 'Error' }))
        }
      })

    getPortfolios()
      .then(res => {
        const ports = res.data
        if (ports && ports.length > 0) {
          const pt = ports[0]
          const pct = pt.total_gain_loss_pct != null ? `${pt.total_gain_loss_pct > 0 ? '+' : ''}${pt.total_gain_loss_pct}%` : '0%'
          setStats(s => ({ ...s, port: pct }))
        } else {
          setStats(s => ({ ...s, port: 'No assets' }))
        }
      })
      .catch(() => setStats(s => ({ ...s, port: '?' })))
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('artha_token')
    navigate('/login')
  }

  return (
    <div className="dash-page">
      <ConstellationBg />

      {/* ── Navbar ──────────────────────────────────── */}
      <nav className="dash-nav">
        <div className="dash-nav-inner">
          <div className="dash-logo">
            <div className="dash-logo-icon">₹</div>
            <span>Dinero</span>
            <span className="dash-badge-beta">Beta</span>
          </div>
          <div className="dash-nav-actions">
            <button className="dash-btn-ghost" onClick={handleLogout}>
              <IconLogout /> Sign out
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ────────────────────────────────────── */}
      <div className="dash-hero">
        <div className="dash-hero-inner">
          <div className="dash-welcome-badge">
            <span className="pulse-dot" />
            Welcome back
          </div>
          <h1 className="dash-hero-title">
            Your Financial <span className="text-gradient">Command Center</span>
          </h1>
          <p className="dash-hero-sub">
            All your personalized financial tools in one place. Each module uses your real data to give you actionable insights.
          </p>
        </div>
      </div>

      {/* ── Quick Stats ─────────────────────────────── */}
      <div className="dash-container">
        <div className="dash-stats-row">
          {[
            ['🔥', 'FIRE Goal', stats.fire],
            ['🩺', 'Health Score', stats.health],
            ['🧾', 'Tax Regime', stats.tax],
            ['📈', 'Portfolio', stats.port],
          ].map(([icon, label, value], i) => (
            <div key={label} className="dash-stat-card" style={{ animationDelay: `${i * 0.08}s` }}>
              <div className="dash-stat-icon">{icon}</div>
              <div className="dash-stat-value">{value}</div>
              <div className="dash-stat-label">{label}</div>
            </div>
          ))}
        </div>

        {/* ── Feature Grid ───────────────────────────── */}
        <h2 className="dash-section-title">Explore Modules</h2>
        <div className="dash-grid">
          {FEATURES.map(({ id, emoji, title, desc, color, border, route }, i) => (
            <button
              key={id}
              onClick={() => navigate(route)}
              className="dash-feature-card"
              style={{ '--card-color': color, '--card-border': border, animationDelay: `${0.1 + i * 0.06}s` }}
              aria-label={`Open ${title}`}
            >
              <div className="dash-card-glow" />
              <div className="dash-card-content">
                <div className="dash-card-emoji">{emoji}</div>
                <h3 className="dash-card-title">{title}</h3>
                <p className="dash-card-desc">{desc}</p>
                <div className="dash-card-link" style={{ color }}>
                  Explore <IconArrow />
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="dash-footer">
        Dinero · Built for the 98% of Indians who make financial decisions alone
      </div>
    </div>
  )
}
