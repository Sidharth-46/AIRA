import { useEffect, useState, useRef } from 'react'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { HiOutlineRefresh, HiOutlineExternalLink, HiX } from 'react-icons/hi'

export default function PreviewPanel() {
  const { previewOpen, togglePreview, fileTree, activeFile, openFiles } = useWorkspaceStore()
  const [previewUrl, setPreviewUrl] = useState('')
  const [srcDoc, setSrcDoc] = useState('')
  const [isVite, setIsVite] = useState(false)
  const iframeRef = useRef(null)

  useEffect(() => {
    if (!previewOpen) return

    const files = fileTree.map(f => f.name)
    
    // Check if it's a Vite/React app
    if (files.includes('package.json') && files.includes('vite.config.js') || files.includes('vite.config.ts')) {
      setIsVite(true)
      // Assuming Vite runs on port 5173 inside the container, we might need a proxy or mapping.
      // For now, we'll assume it's exposed or accessible via localhost for simplicity if running locally,
      // but in a real Docker setup it needs a proxy.
      setPreviewUrl('http://localhost:5173')
    } else if (files.includes('index.html')) {
      // Static HTML project
      setIsVite(false)
      const indexFile = openFiles.find(f => f.name === 'index.html')
      if (indexFile && indexFile.content) {
        setSrcDoc(indexFile.content)
      } else {
        setSrcDoc('<h1>index.html found but not open or loaded.</h1>')
      }
    } else {
      setIsVite(false)
      setSrcDoc('<h1>No preview available for this project type.</h1>')
    }
  }, [previewOpen, fileTree, openFiles])

  const handleRefresh = () => {
    if (iframeRef.current) {
      if (isVite) {
        iframeRef.current.src = iframeRef.current.src
      } else {
        // re-trigger srcDoc update
        const indexFile = openFiles.find(f => f.name === 'index.html')
        if (indexFile) setSrcDoc(indexFile.content + ' ') // slight mutation to trigger reload
      }
    }
  }

  if (!previewOpen) return null

  return (
    <div className="flex flex-col h-full bg-aira-surface w-full border-l border-aira-border relative">
      {/* Header */}
      <div className="flex items-center justify-between px-3 h-10 border-b border-aira-border bg-aira-surface-2 text-xs">
        <div className="flex items-center gap-2 text-aira-text-muted">
          <span className="font-semibold tracking-wider text-[10px]">PREVIEW</span>
          <span className="opacity-50">|</span>
          <span className="truncate max-w-[200px]">{isVite ? previewUrl : 'Static HTML'}</span>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={handleRefresh} className="p-1 hover:bg-aira-surface-3 rounded text-aira-text-dim hover:text-aira-text">
            <HiOutlineRefresh className="w-4 h-4" />
          </button>
          {isVite && (
            <a href={previewUrl} target="_blank" rel="noreferrer" className="p-1 hover:bg-aira-surface-3 rounded text-aira-text-dim hover:text-aira-text">
              <HiOutlineExternalLink className="w-4 h-4" />
            </a>
          )}
          <button onClick={togglePreview} className="p-1 hover:bg-aira-surface-3 rounded text-aira-text-dim hover:text-aira-text">
            <HiX className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 bg-white">
        <iframe
          ref={iframeRef}
          src={isVite ? previewUrl : undefined}
          srcDoc={!isVite ? srcDoc : undefined}
          title="Preview"
          className="w-full h-full border-none"
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
        />
      </div>
    </div>
  )
}
