import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import './Landing.css'

export default function Landing() {
  const canvasRef = useRef(null)

  // Particle Constellation Effect
  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    let animationFrameId
    let particles = []

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    
    window.addEventListener('resize', resize)
    resize()

    // Create particles
    const particleCount = Math.floor((canvas.width * canvas.height) / 12000)
    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        radius: Math.random() * 1.5 + 0.5,
        color: Math.random() > 0.8 ? '#16A34A' : '#3B82F6' // Green or Blue dots
      })
    }

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      
      // Update & Draw Particles
      for (let i = 0; i < particles.length; i++) {
        let p = particles[i]
        p.x += p.vx
        p.y += p.vy
        
        // Bounce off edges
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1
        
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
        ctx.fillStyle = p.color
        ctx.fill()
        
        // Connect nearby particles
        for (let j = i + 1; j < particles.length; j++) {
          let p2 = particles[j]
          let dx = p.x - p2.x
          let dy = p.y - p2.y
          let distance = Math.sqrt(dx * dx + dy * dy)
          
          if (distance < 120) {
            ctx.beginPath()
            ctx.moveTo(p.x, p.y)
            ctx.lineTo(p2.x, p2.y)
            ctx.strokeStyle = `rgba(255, 255, 255, ${0.15 - distance / 800})`
            ctx.lineWidth = 0.5
            ctx.stroke()
          }
        }
      }
      animationFrameId = requestAnimationFrame(draw)
    }
    
    draw()

    return () => {
      window.removeEventListener('resize', resize)
      cancelAnimationFrame(animationFrameId)
    }
  }, [])

  return (
    <div className="landing-page dark">
      {/* Dynamic Background */}
      <canvas ref={canvasRef} className="landing-canvas" />

      {/* Nav */}
      <nav className="landing-nav">
        <div className="landing-logo">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v20"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
          Dinero
        </div>
        <Link to="/login" className="btn btn-primary btn-sm btn-glow">Sign In</Link>
      </nav>

      <main className="landing-content">
        {/* Hero Section */}
        <section className="hero-section">
          <div className="trust-badge">
            <span className="dot pulse-green"></span> Trusted by 50,000+ Indians
          </div>
          <h1 className="hero-title">
            Welcome to <span className="text-dinero-green">Dinero</span>
          </h1>
          <p className="hero-subtitle">
            Your AI-powered personal finance mentor — built for everyday Indians who deserve professional-grade planning.
          </p>
          <div className="hero-ctas">
            <Link to="/signup" className="btn btn-primary btn-lg btn-glow" style={{ borderRadius: '9999px' }}>
              Get Started Free <span style={{ marginLeft: 6 }}>→</span>
            </Link>
            <button className="btn btn-lg btn-outline-glass" style={{ borderRadius: '9999px' }}>
              See how it works
            </button>
          </div>
        </section>

        {/* --- Scroll down for features --- */}
        <section className="features-showcase">
          {/* Feature 1 */}
          <div className="feature-row">
            <div className="feature-text">
              <div className="module-badge module-orange">MODULE 01</div>
              <h2 className="feature-title text-orange-serif">FIRE Path Planner</h2>
              <p className="feature-desc">
                Simulate wealth growth using compound interest. Get your personalised monthly SIP amount and see exactly when you reach financial freedom — with full inflation adjustment.
              </p>
              <Link to="/signup" className="feature-link text-orange">Explore module →</Link>
            </div>
            
            <div className="feature-visual mock-chart-card">
               {/* Pure CSS/SVG Chart mock */}
               <div className="mock-chart-container">
                 <div className="chart-line-orange"></div>
                 <div className="chart-fade-orange"></div>
               </div>
               
               {/* Play Button Overlay */}
               <div className="play-button-overlay">
                 <div className="play-triangle"></div>
               </div>
            </div>
          </div>

          {/* Feature 2 */}
          <div className="feature-row reverse">
            <div className="feature-visual mock-health-card">
               {/* Pure CSS Circular Progress mock */}
               <div className="health-circle-wrapper">
                 <svg className="health-circle" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="40" className="track"></circle>
                    <circle cx="50" cy="50" r="40" className="progress"></circle>
                 </svg>
                 <div className="health-circle-text">
                   <div className="score">78</div>
                   <div className="outof">out of 100</div>
                 </div>
               </div>
               <div className="health-status">Good — 2 gaps found</div>
            </div>

            <div className="feature-text">
              <div className="module-badge module-green">MODULE 02</div>
              <h2 className="feature-title text-green-serif">Money Health Score</h2>
              <p className="feature-desc">
                Score your financial wellness across 6 deep dimensions — emergency fund coverage, insurance adequacy, debt ratio, tax efficiency, portfolio diversification, and retirement readiness.
              </p>
              <Link to="/signup" className="feature-link text-green">Explore module →</Link>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
