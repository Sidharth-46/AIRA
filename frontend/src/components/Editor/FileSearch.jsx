import { useState, useEffect, useRef } from 'react'
import Modal from '../Common/Modal'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { HiOutlineSearch, HiDocument } from 'react-icons/hi'

export default function FileSearch() {
  const { fileSearchOpen, setFileSearchOpen, fileTree, openFile } = useWorkspaceStore()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef(null)

  // Flatten tree to searchable list
  const flattenTree = (nodes, path = '') => {
    let list = []
    for (const node of nodes) {
      if (node.type === 'file') {
        list.push(node)
      } else if (node.children) {
        list = list.concat(flattenTree(node.children, node.path))
      }
    }
    return list
  }

  useEffect(() => {
    if (fileSearchOpen) {
      setTimeout(() => inputRef.current?.focus(), 100)
      setQuery('')
      setSelectedIndex(0)
      
      // Default to showing all files if empty query
      const allFiles = flattenTree(fileTree)
      setResults(allFiles.slice(0, 10)) 
    }
  }, [fileSearchOpen, fileTree])

  useEffect(() => {
    if (!query) {
      setResults(flattenTree(fileTree).slice(0, 10))
      return
    }

    const allFiles = flattenTree(fileTree)
    const lowerQ = query.toLowerCase()
    
    // Simple fuzzy match by filename or path
    const filtered = allFiles.filter(f => 
      f.name.toLowerCase().includes(lowerQ) || 
      f.path.toLowerCase().includes(lowerQ)
    ).slice(0, 10) // limit to 10
    
    setResults(filtered)
    setSelectedIndex(0)
  }, [query, fileTree])

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
        handleSelect(results[selectedIndex])
      }
    }
  }

  const handleSelect = (file) => {
    openFile(file)
    setFileSearchOpen(false)
  }

  return (
    <Modal isOpen={fileSearchOpen} onClose={() => setFileSearchOpen(false)} title="Search Files (Ctrl+P)">
      <div className="relative mb-4">
        <HiOutlineSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-aira-text-dim" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type to search files..."
          className="w-full bg-aira-surface-2 border border-aira-border rounded-lg py-2 pl-10 pr-4 text-sm focus:border-aira-primary focus:outline-none"
        />
      </div>

      <div className="max-h-[60vh] overflow-y-auto">
        {results.length > 0 ? (
          <ul className="space-y-1">
            {results.map((file, idx) => (
              <li
                key={file.path}
                onClick={() => handleSelect(file)}
                onMouseEnter={() => setSelectedIndex(idx)}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-sm ${
                  selectedIndex === idx ? 'bg-aira-primary/20 text-aira-text' : 'text-aira-text-muted hover:bg-aira-surface-3'
                }`}
              >
                <HiDocument className="text-aira-text-dim flex-shrink-0" />
                <div className="flex-1 overflow-hidden">
                  <div className="truncate text-aira-text">{file.name}</div>
                  <div className="truncate text-xs opacity-50">{file.path}</div>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="text-center py-8 text-aira-text-dim text-sm">
            No files found matching "{query}"
          </div>
        )}
      </div>
    </Modal>
  )
}
