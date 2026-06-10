import { useEffect } from 'react'
import { useWorkspaceStore } from '../stores/workspaceStore'

export function useKeyboardShortcuts() {
  const { 
    toggleCommandPalette, 
    toggleFileSearch, 
    toggleGlobalSearch, 
    toggleSidebar,
    activeFile,
    saveFile
  } = useWorkspaceStore()

  useEffect(() => {
    const handleKeyDown = (e) => {
      // Command Palette: Ctrl+K or Cmd+K
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        toggleCommandPalette()
      }
      
      // File Search: Ctrl+P or Cmd+P
      else if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        e.preventDefault()
        toggleFileSearch()
      }
      
      // Global Search: Ctrl+Shift+F or Cmd+Shift+F
      else if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'f') {
        e.preventDefault()
        toggleGlobalSearch()
      }
      
      // Save File: Ctrl+S or Cmd+S
      else if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault()
        if (activeFile) {
          saveFile(activeFile.path)
        }
      }
      
      // Toggle Sidebar: Ctrl+B or Cmd+B
      else if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        e.preventDefault()
        toggleSidebar()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [toggleCommandPalette, toggleFileSearch, toggleGlobalSearch, toggleSidebar, activeFile, saveFile])
}
