import { useEffect, useRef, useState } from 'react'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import {
  HiOutlineDocumentAdd,
  HiOutlineFolderAdd,
  HiOutlinePencil,
  HiOutlineTrash,
  HiOutlineClipboardCopy,
} from 'react-icons/hi'

export default function ContextMenu() {
  const { contextMenu, hideContextMenu, createFile, deleteFileFromTree, renameFile, activeProjectId, refreshTree } =
    useWorkspaceStore()
  const menuRef = useRef(null)
  const [renaming, setRenaming] = useState(false)
  const [newName, setNewName] = useState('')
  const [creating, setCreating] = useState(null) // 'file' | 'folder' | null
  const [createName, setCreateName] = useState('')

  // Close on outside click
  useEffect(() => {
    const handleClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        hideContextMenu()
        setRenaming(false)
        setCreating(null)
      }
    }
    if (contextMenu) {
      document.addEventListener('mousedown', handleClick)
    }
    return () => document.removeEventListener('mousedown', handleClick)
  }, [contextMenu, hideContextMenu])

  if (!contextMenu) return null

  const { x, y, node } = contextMenu

  const handleCopyPath = () => {
    navigator.clipboard.writeText(node.path)
    hideContextMenu()
  }

  const handleDelete = async () => {
    if (window.confirm(`Delete "${node.name}"?`)) {
      try {
        await deleteFileFromTree(node.path)
      } catch { /* handled in store */ }
    }
    hideContextMenu()
  }

  const handleRenameStart = () => {
    setNewName(node.name)
    setRenaming(true)
  }

  const handleRenameSubmit = async (e) => {
    e.preventDefault()
    if (!newName.trim() || newName === node.name) {
      setRenaming(false)
      hideContextMenu()
      return
    }
    const parentPath = node.path.includes('/')
      ? node.path.substring(0, node.path.lastIndexOf('/'))
      : ''
    const newPath = parentPath ? `${parentPath}/${newName}` : newName
    try {
      await renameFile(node.path, newPath)
    } catch { /* handled in store */ }
    setRenaming(false)
    hideContextMenu()
  }

  const handleCreateStart = (type) => {
    setCreating(type)
    setCreateName('')
  }

  const handleCreateSubmit = async (e) => {
    e.preventDefault()
    if (!createName.trim()) {
      setCreating(null)
      hideContextMenu()
      return
    }
    const basePath = node.type === 'directory' ? node.path : (
      node.path.includes('/') ? node.path.substring(0, node.path.lastIndexOf('/')) : ''
    )
    const fullPath = basePath ? `${basePath}/${createName}` : createName
    try {
      await createFile(fullPath, creating === 'folder', '')
    } catch { /* handled in store */ }
    setCreating(null)
    hideContextMenu()
  }

  // Position the menu, clamping to viewport
  const menuStyle = {
    position: 'fixed',
    top: Math.min(y, window.innerHeight - 280),
    left: Math.min(x, window.innerWidth - 220),
    zIndex: 1000,
  }

  return (
    <div ref={menuRef} className="context-menu" style={menuStyle}>
      {renaming ? (
        <form onSubmit={handleRenameSubmit} className="context-menu-form">
          <input
            autoFocus
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === 'Escape' && (setRenaming(false), hideContextMenu())}
            className="context-menu-input"
            placeholder="New name..."
          />
        </form>
      ) : creating ? (
        <form onSubmit={handleCreateSubmit} className="context-menu-form">
          <input
            autoFocus
            value={createName}
            onChange={(e) => setCreateName(e.target.value)}
            onKeyDown={(e) => e.key === 'Escape' && (setCreating(null), hideContextMenu())}
            className="context-menu-input"
            placeholder={creating === 'folder' ? 'Folder name...' : 'File name...'}
          />
        </form>
      ) : (
        <>
          <button className="context-menu-item" onClick={() => handleCreateStart('file')}>
            <HiOutlineDocumentAdd className="w-4 h-4" /> New File
          </button>
          <button className="context-menu-item" onClick={() => handleCreateStart('folder')}>
            <HiOutlineFolderAdd className="w-4 h-4" /> New Folder
          </button>
          <div className="context-menu-separator" />
          <button className="context-menu-item" onClick={handleRenameStart}>
            <HiOutlinePencil className="w-4 h-4" /> Rename
          </button>
          <button className="context-menu-item context-menu-item-danger" onClick={handleDelete}>
            <HiOutlineTrash className="w-4 h-4" /> Delete
          </button>
          <div className="context-menu-separator" />
          <button className="context-menu-item" onClick={handleCopyPath}>
            <HiOutlineClipboardCopy className="w-4 h-4" /> Copy Path
          </button>
        </>
      )}
    </div>
  )
}
