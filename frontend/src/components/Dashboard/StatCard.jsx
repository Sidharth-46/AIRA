import { useState, useEffect } from 'react'

export default function StatCard({ title, value, icon: Icon, color }) {
  const [count, setCount] = useState(0)
  const safeValue = typeof value === 'number' && !isNaN(value) ? value : 0

  useEffect(() => {
    if (safeValue === 0) { setCount(0); return }
    let start = 0
    const steps = Math.max(1000 / 16, 1)
    const increment = safeValue / steps
    const timer = setInterval(() => {
      start += increment
      if (start >= safeValue) { setCount(safeValue); clearInterval(timer) }
      else setCount(Math.floor(start))
    }, 16)
    return () => clearInterval(timer)
  }, [safeValue])

  return (
    <div className="card" style={{ height: '140px', padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: '14px', fontWeight: 500, color: 'var(--color-aira-text-muted)' }}>
          {title}
        </span>
        <Icon style={{ fontSize: '20px', color: color || 'var(--color-aira-text-dim)' }} />
      </div>
      <div style={{ fontSize: '36px', fontWeight: 700, color: 'var(--color-aira-text)' }}>
        {count}
      </div>
    </div>
  )
}
