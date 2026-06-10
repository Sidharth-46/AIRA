import { useRef, useEffect } from 'react'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { HiX, HiOutlineTerminal } from 'react-icons/hi'

export default function Terminal() {
  const { logs, terminalOpen, toggleTerminal, clearLogs } = useWorkspaceStore()
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs, terminalOpen])

  if (!terminalOpen) return null

  return (
    <div className="h-48 flex flex-col bg-aira-bg border-t border-aira-border">
      {/* Terminal Header */}
      <div className="flex items-center justify-between px-4 py-1.5 bg-aira-surface-2 border-b border-aira-border">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-aira-text-muted">
          <HiOutlineTerminal className="text-sm" />
          Terminal Output
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={clearLogs}
            className="text-xs text-aira-text-dim hover:text-aira-text transition-colors"
          >
            Clear
          </button>
          <button 
            onClick={toggleTerminal}
            className="p-1 hover:bg-white/10 rounded transition-colors text-aira-text-dim"
          >
            <HiX className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Terminal Body */}
      <div className="flex-1 overflow-y-auto p-2 font-mono text-sm">
        {logs.length === 0 ? (
          <div className="text-aira-text-dim text-xs opacity-50">AIRA Terminal - Waiting for output...</div>
        ) : (
          logs.map(log => (
            <div 
              key={log.id} 
              className={`mb-1 flex gap-3 ${
                log.type === 'error' ? 'text-red-400' : 
                log.type === 'success' ? 'text-green-400' : 
                log.type === 'warn' ? 'text-yellow-400' : 
                'text-aira-text'
              }`}
            >
              <span className="text-aira-text-dim opacity-50 flex-shrink-0">
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
              <span className="whitespace-pre-wrap">{log.msg}</span>
            </div>
          ))
        )}
        <div ref={endRef} />
      </div>
    </div>
  )
}
