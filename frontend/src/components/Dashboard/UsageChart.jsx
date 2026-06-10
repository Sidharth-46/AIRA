export default function UsageChart({ data }) {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <div style={{ 
        height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center',
        border: '1px dashed var(--color-aira-border)', borderRadius: '8px',
      }}>
        <p style={{ fontSize: '13px', color: 'var(--color-aira-text-dim)' }}>No usage data available</p>
      </div>
    )
  }

  const maxCount = Math.max(...data.map(d => (typeof d.count === 'number' && !isNaN(d.count) ? d.count : 0)), 10)
  
  return (
    <div style={{ height: '200px', display: 'flex', alignItems: 'flex-end', gap: '8px', padding: '0 4px' }}>
      {data.map((item, idx) => {
        const safeCount = typeof item.count === 'number' && !isNaN(item.count) ? item.count : 0
        const pct = (safeCount / maxCount) * 100
        return (
          <div key={idx} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', height: '100%', justifyContent: 'flex-end' }}>
            <div 
              style={{ 
                width: '100%', 
                maxWidth: '40px',
                height: `${Math.max(pct, 4)}%`,
                background: 'var(--color-aira-primary)',
                borderRadius: '4px 4px 0 0',
                transition: 'height 0.5s ease-out',
                opacity: 0.8,
              }}
              title={`${safeCount} interactions`}
            />
            <span style={{ fontSize: '12px', color: 'var(--color-aira-text-dim)' }}>
              {item.date || ''}
            </span>
          </div>
        )
      })}
    </div>
  )
}
