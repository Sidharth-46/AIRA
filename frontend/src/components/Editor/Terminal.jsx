import { useRef, useEffect, useState } from 'react'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { useAuthStore } from '../../stores/authStore'
import { Terminal as XTerm } from 'xterm'
import { FitAddon } from '@xterm/addon-fit'
import { io } from 'socket.io-client'
import 'xterm/css/xterm.css'
import {
  HiOutlineTerminal,
  HiOutlineExclamation,
  HiOutlineInformationCircle,
  HiX,
} from 'react-icons/hi'

const TABS = [
  { id: 'terminal', label: 'Terminal', icon: HiOutlineTerminal },
  { id: 'problems', label: 'Problems', icon: HiOutlineExclamation },
  { id: 'output', label: 'Output', icon: HiOutlineInformationCircle },
]

function RealTerminal() {
  const terminalRef = useRef(null)
  const xtermRef = useRef(null)
  const socketRef = useRef(null)
  const fitAddonRef = useRef(null)
  const { activeProjectId } = useWorkspaceStore()
  const token = localStorage.getItem('aira_token')

  useEffect(() => {
    if (!terminalRef.current) return

    // Initialize xterm
    const xterm = new XTerm({
      cursorBlink: true,
      fontFamily: 'var(--font-mono)',
      fontSize: 13,
      theme: {
        background: 'transparent',
        foreground: '#ffffff',
      },
    })
    
    const fitAddon = new FitAddon()
    xterm.loadAddon(fitAddon)
    xterm.open(terminalRef.current)
    fitAddon.fit()

    xtermRef.current = xterm
    fitAddonRef.current = fitAddon

    // Connect socket
    const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000'
    const socket = io(`${backendUrl}/ws/terminal`, {
      transports: ['websocket'],
    })

    socket.on('connect', () => {
      socket.emit('start', { token, project: activeProjectId })
    })

    socket.on('terminal_output', (data) => {
      if (data && data.data) {
        xterm.write(data.data)
      }
    })

    xterm.onData((data) => {
      socket.emit('terminal_input', { data })
    })

    xterm.onResize(({ cols, rows }) => {
      socket.emit('resize', { cols, rows })
    })

    socketRef.current = socket

    const handleResize = () => {
      fitAddon.fit()
    }

    const handleCustomInput = (e) => {
      const cmd = e.detail
      if (socket.connected) {
        socket.emit('terminal_input', { data: cmd })
      }
    }

    window.addEventListener('resize', handleResize)
    document.addEventListener('aira_terminal_input', handleCustomInput)

    // Fit addon when parent resizes using ResizeObserver
    const observer = new ResizeObserver(() => fitAddon.fit())
    observer.observe(terminalRef.current)

    return () => {
      window.removeEventListener('resize', handleResize)
      document.removeEventListener('aira_terminal_input', handleCustomInput)
      observer.disconnect()
      socket.disconnect()
      xterm.dispose()
    }
  }, [activeProjectId, token])

  return <div ref={terminalRef} style={{ width: '100%', height: '100%' }} />
}

export default function BottomPanel() {
  const {
    logs,
    problems,
    terminalOpen,
    toggleTerminal,
    clearLogs,
    bottomPanelTab,
    setBottomPanelTab,
  } = useWorkspaceStore()

  const endRef = useRef(null)

  useEffect(() => {
    if (bottomPanelTab === 'output') {
      endRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs, terminalOpen, bottomPanelTab])

  if (!terminalOpen) return null

  return (
    <div className="bottom-panel">
      {/* Tab Bar */}
      <div className="bottom-panel-tabs">
        <div className="bottom-panel-tabs-left">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              className={`bottom-panel-tab ${bottomPanelTab === tab.id ? 'bottom-panel-tab-active' : ''}`}
              onClick={() => setBottomPanelTab(tab.id)}
            >
              <tab.icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
              {tab.id === 'problems' && problems.length > 0 && (
                <span className="bottom-panel-badge">{problems.length}</span>
              )}
            </button>
          ))}
        </div>
        <div className="bottom-panel-tabs-right">
          {bottomPanelTab === 'output' && (
            <button onClick={clearLogs} className="bottom-panel-action" title="Clear">
              Clear
            </button>
          )}
          <button onClick={toggleTerminal} className="bottom-panel-action" title="Close Panel">
            <HiX className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="bottom-panel-content">
        {/* Terminal Tab */}
        <div className="bottom-panel-terminal" style={{ display: bottomPanelTab === 'terminal' ? 'block' : 'none' }}>
          <RealTerminal />
        </div>

        {/* Problems Tab */}
        {bottomPanelTab === 'problems' && (
          <div className="bottom-panel-problems">
            {problems.length === 0 ? (
              <div className="bottom-panel-empty">
                <HiOutlineExclamation className="w-4 h-4 opacity-40" />
                <span>No problems detected</span>
              </div>
            ) : (
              problems.map((p, i) => (
                <div key={i} className="problem-item">
                  <HiOutlineExclamation
                    className={`w-4 h-4 ${p.severity === 'error' ? 'text-red-400' : 'text-yellow-400'}`}
                  />
                  <span className="problem-message">{p.message}</span>
                  <span className="problem-file">{p.file}</span>
                </div>
              ))
            )}
          </div>
        )}

        {/* Output Tab */}
        {bottomPanelTab === 'output' && (
          <div className="bottom-panel-output">
            {logs.length === 0 ? (
              <div className="bottom-panel-empty">
                <HiOutlineInformationCircle className="w-4 h-4 opacity-40" />
                <span>AIRA system output will appear here</span>
              </div>
            ) : (
              logs.map((log) => (
                <div
                  key={log.id}
                  className={`terminal-line ${
                    log.type === 'error'
                      ? 'terminal-line-error'
                      : log.type === 'success'
                      ? 'terminal-line-success'
                      : log.type === 'warn'
                      ? 'terminal-line-warn'
                      : ''
                  }`}
                >
                  <span className="terminal-timestamp">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  <span className="terminal-text">{log.msg}</span>
                </div>
              ))
            )}
            <div ref={endRef} />
          </div>
        )}
      </div>
    </div>
  )
}
