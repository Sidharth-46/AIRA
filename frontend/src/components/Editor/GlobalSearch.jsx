import { useState, useEffect, useRef } from 'react'
import Modal from '../Common/Modal'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { workspaceService } from '../../services'
import { HiOutlineSearch, HiDocumentText } from 'react-icons/hi'
import { useSearchParams } from 'react-router-dom'

export default function GlobalSearch() {
  const { globalSearchOpen, setGlobalSearchOpen, openFile } = useWorkspaceStore()
  const [searchParams] = useSearchParams()
  const projectId = searchParams.get('project')
  
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const inputRef = useRef(null)

  useEffect(() => {
    if (globalSearchOpen) {
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [globalSearchOpen])

  useEffect(() => {
    const delayDebounceFn = setTimeout(async () => {
      if (query.length > 2 && projectId) {
        setLoading(true)
        try {
          const res = await workspaceService.search(query, projectId)
          setResults(res.data.results || [])
        } catch (err) {
          console.error('Search failed', err)
          setResults([])
        } finally {
          setLoading(false)
        }
      } else {
        setResults([])
      }
    }, 500)

    return () => clearTimeout(delayDebounceFn)
  }, [query, projectId])

  const handleSelect = (filePath) => {
    // Basic mock of opening file from global search
    openFile({ path: filePath, name: filePath.split('/').pop(), type: 'file' })
    setGlobalSearchOpen(false)
  }

  return (
    <Modal isOpen={globalSearchOpen} onClose={() => setGlobalSearchOpen(false)} title="Global Search (Ctrl+Shift+F)" maxWidth="xl">
      <div className="relative mb-6">
        <HiOutlineSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-aira-text-dim text-lg" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search across all files (min 3 chars)..."
          className="w-full bg-aira-surface-2 border border-aira-border rounded-lg py-3 pl-10 pr-4 text-sm focus:border-aira-primary focus:outline-none shadow-inner"
        />
      </div>

      <div className="max-h-[60vh] overflow-y-auto pr-2">
        {loading ? (
          <div className="text-center py-8 text-aira-text-dim text-sm flex items-center justify-center gap-2">
            <div className="w-4 h-4 border-2 border-aira-border-light border-t-aira-primary rounded-full animate-spin" />
            Searching...
          </div>
        ) : results.length > 0 ? (
          <div className="space-y-4">
            {results.map((group, idx) => (
              <div key={idx} className="bg-aira-surface-2 rounded-xl overflow-hidden border border-aira-border-light">
                <div 
                  className="px-3 py-2 bg-aira-surface-3 border-b border-aira-border flex items-center gap-2 cursor-pointer hover:bg-aira-surface/80"
                  onClick={() => handleSelect(group.file)}
                >
                  <HiDocumentText className="text-aira-text-dim" />
                  <span className="text-sm font-medium text-aira-text truncate">{group.file}</span>
                </div>
                <div>
                  {group.matches.map((match, i) => (
                    <div 
                      key={i} 
                      className="px-3 py-1.5 text-xs text-aira-text-muted hover:bg-aira-surface cursor-pointer flex gap-4 font-mono"
                      onClick={() => handleSelect(group.file)}
                    >
                      <span className="text-aira-text-dim opacity-50 select-none w-8 text-right shrink-0">{match.line}</span>
                      <span className="truncate">{match.content}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : query.length > 2 ? (
          <div className="text-center py-10 text-aira-text-dim text-sm">
            No matches found for "{query}"
          </div>
        ) : (
          <div className="text-center py-10 text-aira-text-dim text-sm opacity-50">
            Enter at least 3 characters to start searching
          </div>
        )}
      </div>
    </Modal>
  )
}
