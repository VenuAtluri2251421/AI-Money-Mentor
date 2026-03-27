import { useEffect, useRef } from 'react'

/**
 * CursorGlow — A global interactive mouse effect.
 *
 * Renders a soft, coloured radial glow that follows the cursor.
 * On click, spawns a burst of tiny particles that expand outward.
 * Purely decorative — pointer-events: none so it never blocks UI.
 */
export default function CursorGlow() {
  const glowRef = useRef(null)
  const canvasRef = useRef(null)
  const particles = useRef([])
  const mousePos = useRef({ x: -100, y: -100 })
  const rafId = useRef(null)

  useEffect(() => {
    const glow = glowRef.current
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener('resize', resize)

    // Move glow with cursor
    const handleMove = (e) => {
      mousePos.current = { x: e.clientX, y: e.clientY }
      glow.style.transform = `translate(${e.clientX - 200}px, ${e.clientY - 200}px)`
    }

    // Click burst
    const handleClick = (e) => {
      for (let i = 0; i < 12; i++) {
        const angle = (Math.PI * 2 * i) / 12 + Math.random() * 0.3
        const speed = 2 + Math.random() * 3
        particles.current.push({
          x: e.clientX,
          y: e.clientY,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          life: 1,
          color: Math.random() > 0.5 ? '#3B82F6' : '#16A34A',
          radius: 2 + Math.random() * 2,
        })
      }
    }

    window.addEventListener('mousemove', handleMove)
    window.addEventListener('click', handleClick)

    // Animation loop for click-burst particles
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      particles.current = particles.current.filter((p) => {
        p.x += p.vx
        p.y += p.vy
        p.life -= 0.02
        p.vy += 0.05 // gentle gravity
        if (p.life <= 0) return false

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.radius * p.life, 0, Math.PI * 2)
        ctx.fillStyle = p.color
        ctx.globalAlpha = p.life
        ctx.fill()
        ctx.globalAlpha = 1
        return true
      })
      rafId.current = requestAnimationFrame(draw)
    }
    draw()

    return () => {
      window.removeEventListener('mousemove', handleMove)
      window.removeEventListener('click', handleClick)
      window.removeEventListener('resize', resize)
      cancelAnimationFrame(rafId.current)
    }
  }, [])

  return (
    <>
      {/* Radial gradient glow that follows cursor */}
      <div
        ref={glowRef}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: 400,
          height: 400,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(59,130,246,0.12) 0%, rgba(22,163,74,0.06) 40%, transparent 70%)',
          pointerEvents: 'none',
          zIndex: 9999,
          transition: 'transform 0.08s linear',
          willChange: 'transform',
        }}
      />
      {/* Canvas for click-burst particles */}
      <canvas
        ref={canvasRef}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
          zIndex: 9999,
        }}
      />
    </>
  )
}
