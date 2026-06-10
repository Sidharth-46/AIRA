import { HiOutlineMenuAlt2, HiOutlineClock } from 'react-icons/hi'
import { useState, useEffect, useRef } from 'react'
import { modelService } from '../../services'

export default function Header({ toggleSidebar }) {
  const [modelStatus, setModelStatus] = useState({ connected: false, model: null })
  const [isConnecting, setIsConnecting] = useState(true)
  const mounted = useRef(true)

  useEffect(() => {
    return () => { mounted.current = false }
  }, [])

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await modelService.getStatus()
        if (!mounted.current) return
        
        const data = res.data.ollama || res.data?.data?.ollama
        if (data?.connected) {
          setModelStatus(data)
          setIsConnecting(false)
        } else {
          setModelStatus({ connected: false, model: null })
          setIsConnecting(false)
        }
      } catch (err) {
        if (!mounted.current) return
        setModelStatus({ connected: false, model: null })
        setIsConnecting(false)
      }
    }
    
    fetchStatus()
    const interval = setInterval(fetchStatus, 15000)
    return () => clearInterval(interval)
  }, [])

  return (
    <header 
      className="flex items-center justify-between sticky top-0 z-30"
      style={{ 
        height: '64px', 
        padding: '0 24px', 
        background: 'var(--color-aira-bg)', 
        borderBottom: '1px solid var(--color-aira-border)' 
      }}
    >
      <div className="flex items-center gap-3">
        <button 
          onClick={toggleSidebar}
          className="lg:hidden flex items-center justify-center transition-colors"
          style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'transparent', border: 'none', color: 'var(--color-aira-text)', cursor: 'pointer' }}
          onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-aira-surface-3)' }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent' }}
        >
          <HiOutlineMenuAlt2 style={{ fontSize: '20px' }} />
        </button>
      </div>

      {/* Model Status */}
      <div className="flex items-center gap-2" style={{ fontSize: '13px', color: 'var(--color-aira-text-muted)' }}>
        <span 
          style={{ 
            width: '8px', 
            height: '8px', 
            borderRadius: '50%', 
            background: modelStatus?.connected ? '#22C55E' : isConnecting ? '#F59E0B' : '#EF4444',
            display: 'inline-block'
          }} 
        />
        <span>
          {modelStatus?.connected 
            ? (modelStatus.model ?? 'Connected') 
            : isConnecting 
              ? 'Connecting...' 
              : 'Disconnected'}
        </span>
      </div>
    </header>
  )
}
