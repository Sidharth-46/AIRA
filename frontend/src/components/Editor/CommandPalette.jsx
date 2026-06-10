import { useState, useEffect, useRef } from 'react'
import Modal from '../Common/Modal'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { useThemeStore } from '../../stores/themeStore'
import { HiOutlineTerminal, HiOutlineMoon, HiOutlineSun, HiOutlineChatAlt2 } from 'react-icons/hi'
import { useNavigate } from 'react-router-dom'

export default function CommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen, toggleTerminal, toggleSidebar } = useWorkspaceStore()
  const { theme, toggleTheme } = useThemeStore()
  const navigate = useNavigate()
  
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef(null)

  const allCommands = [
    { id: 'terminal', title: 'Toggle Terminal', icon: HiOutlineTerminal, action: toggleTerminal },
    { id: 'sidebar', title: 'Toggle Sidebar', icon: HiOutlineTerminal, action: toggleSidebar },
    { id: 'theme', title: `Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`, icon: theme === 'dark' ? HiOutlineSun : HiOutlineMoon, action: toggleTheme },
    { id: 'new_chat', title: 'New Chat', icon: HiOutlineChatAlt2, action: () => navigate('/chat') },
    { id: 'dashboard', title: 'Go to Dashboard', icon: HiOutlineTerminal, action: () => navigate('/dashboard') },
    { id: 'projects', title: 'Go to Projects', icon: HiOutlineTerminal, action: () => navigate('/projects') },
  ]

  const [results, setResults] = useState(allCommands)

  useEffect(() => {
    if (commandPaletteOpen) {
      setTimeout(() => inputRef.current?.focus(), 100)
      setQuery('')
      setSelectedIndex(0)
      setResults(allCommands)
    }
  }, [commandPaletteOpen, theme]) // Also re-run if theme changes to update label

  useEffect(() => {
    if (!query) {
      setResults(allCommands)
      return
    }
    const lowerQ = query.toLowerCase()
    setResults(allCommands.filter(c => c.title.toLowerCase().includes(lowerQ)))
    setSelectedIndex(0)
  }, [query])

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex(prev => Math.min(prev + 1, results.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex(prev => Math.max(prev - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (results[selectedIndex]) {
        results[selectedIndex].action()
        setCommandPaletteOpen(false)
      }
    }
  }

  return (
    <Modal isOpen={commandPaletteOpen} onClose={() => setCommandPaletteOpen(false)} title="Command Palette (Ctrl+K)">
      <div className="relative mb-4">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-aira-text-dim text-lg">&gt;</span>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a command..."
          className="w-full bg-aira-surface-2 border border-aira-border rounded-lg py-3 pl-8 pr-4 text-sm focus:border-aira-primary focus:outline-none shadow-inner"
        />
      </div>

      <div className="max-h-[50vh] overflow-y-auto">
        {results.length > 0 ? (
          <ul className="space-y-1">
            {results.map((cmd, idx) => (
              <li
                key={cmd.id}
                onClick={() => {
                  cmd.action()
                  setCommandPaletteOpen(false)
                }}
                onMouseEnter={() => setSelectedIndex(idx)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer text-sm transition-colors ${
                  selectedIndex === idx ? 'bg-aira-primary/20 text-aira-text' : 'text-aira-text-muted hover:bg-aira-surface-3'
                }`}
              >
                <cmd.icon className="text-aira-text-dim text-lg" />
                <span>{cmd.title}</span>
              </li>
            ))}
          </ul>
        ) : (
          <div className="text-center py-8 text-aira-text-dim text-sm">
            No commands found
          </div>
        )}
      </div>
    </Modal>
  )
}
