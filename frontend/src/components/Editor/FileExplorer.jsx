import { useState } from 'react'
import { 
  HiOutlineChevronRight, HiOutlineChevronDown, HiOutlineDocument, HiOutlineFolder, 
  HiOutlineFolderOpen 
} from 'react-icons/hi'
import { useWorkspaceStore } from '../../stores/workspaceStore'

// Helper recursive component for tree nodes
const FileTreeNode = ({ node, level = 0 }) => {
  const [isOpen, setIsOpen] = useState(false)
  const { openFile, activeFile } = useWorkspaceStore()
  
  const isDir = node.type === 'directory'
  const isActive = activeFile?.path === node.path

  const toggleOpen = (e) => {
    e.stopPropagation()
    setIsOpen(!isOpen)
  }

  const handleSelect = (e) => {
    e.stopPropagation()
    if (isDir) {
      setIsOpen(!isOpen)
    } else {
      openFile(node)
    }
  }

  return (
    <div>
      <div 
        className={`flex items-center py-1 px-2 hover:bg-aira-surface-3 cursor-pointer select-none text-sm transition-colors ${
          isActive ? 'bg-aira-surface-3 text-aira-text' : 'text-aira-text-muted'
        }`}
        style={{ paddingLeft: `${level * 12 + 8}px` }}
        onClick={handleSelect}
      >
        <span className="w-4 h-4 mr-1 flex items-center justify-center" onClick={isDir ? toggleOpen : undefined}>
          {isDir ? (
            isOpen ? <HiOutlineChevronDown className="w-3 h-3" /> : <HiOutlineChevronRight className="w-3 h-3" />
          ) : null}
        </span>
        
        <span className="w-4 h-4 mr-2 flex items-center justify-center">
          {isDir ? (
            isOpen ? <HiOutlineFolderOpen className="text-aira-accent-2" /> : <HiOutlineFolder className="text-aira-accent-2" />
          ) : (
            <HiOutlineDocument className="text-aira-text-dim" />
          )}
        </span>
        
        <span className="truncate">{node.name}</span>
      </div>

      {isDir && isOpen && node.children && (
        <div>
          {/* Sort: directories first, then files */}
          {[...node.children]
            .sort((a, b) => {
              if (a.type === b.type) return a.name.localeCompare(b.name)
              return a.type === 'directory' ? -1 : 1
            })
            .map(child => (
              <FileTreeNode key={child.path} node={child} level={level + 1} />
            ))
          }
        </div>
      )}
    </div>
  )
}

export default function FileExplorer() {
  const { fileTree, sidebarOpen } = useWorkspaceStore()

  if (!sidebarOpen) return null

  return (
    <div className="w-64 h-full flex flex-col bg-aira-surface-2 border-r border-aira-border overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-aira-border">
        <span className="text-xs font-semibold uppercase tracking-wider text-aira-text-dim">
          Explorer
        </span>
      </div>
      
      <div className="flex-1 overflow-y-auto py-2">
        {fileTree.length > 0 ? (
          fileTree.map((node) => (
            <FileTreeNode key={node.path} node={node} />
          ))
        ) : (
          <div className="px-4 py-2 text-sm text-aira-text-dim text-center mt-4">
            No folder opened
          </div>
        )}
      </div>
    </div>
  )
}
