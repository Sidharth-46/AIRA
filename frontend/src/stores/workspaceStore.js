import { create } from 'zustand'
import { workspaceService } from '../services'

export const useWorkspaceStore = create((set, get) => ({
  activeProjectId: null,
  activeProjectName: null,
  fileTree: [],
  openFiles: [],
  activeFile: null,
  unsavedFiles: new Set(),
  searchResults: [],
  commandPaletteOpen: false,
  fileSearchOpen: false,
  globalSearchOpen: false,
  terminalOpen: true,
  sidebarOpen: true,
  logs: [],

  setFileTree: (tree) => set({ fileTree: tree }),
  
  refreshTree: async (projectId) => {
    try {
      const res = await workspaceService.getTree(projectId)
      set({ 
        fileTree: res.data.tree, 
        activeProjectId: projectId, 
        activeProjectName: res.data.projectName || null 
      })
    } catch (err) {
      console.error('Failed to fetch tree', err)
    }
  },

  openFile: async (fileNode) => {
    const { openFiles, activeFile } = get()
    
    // Check if already open
    const existing = openFiles.find(f => f.path === fileNode.path)
    if (existing) {
      set({ activeFile: existing })
      return
    }

    try {
      const { activeProjectId } = get()
      console.log(`FILE_OPEN_REQUEST: path=${fileNode.path}, projectId=${activeProjectId}`)
      
      const res = await workspaceService.readFile(fileNode.path, activeProjectId)
      
      console.log("WORKSPACE_RESPONSE_SHAPE", Object.keys(res.data || {}))
      
      const fileData = res.data?.file || res.data?.data?.file || res.data
      const content = typeof fileData?.content === "string" ? fileData.content : null
      
      console.log(`FILE_OPEN_SUCCESS: path=${fileNode.path}, contentLength=${content?.length}`)
      
      const newFile = { ...fileNode, content, originalContent: content }
      set({ 
        openFiles: [...openFiles, newFile],
        activeFile: newFile
      })
    } catch (err) {
      console.error(`FILE_OPEN_FAILURE: path=${fileNode.path}`, err)
    }
  },

  closeFile: (path) => {
    const { openFiles, activeFile, unsavedFiles } = get()
    const newOpenFiles = openFiles.filter(f => f.path !== path)
    
    const newUnsaved = new Set(unsavedFiles)
    newUnsaved.delete(path)

    let newActive = activeFile
    if (activeFile?.path === path) {
      newActive = newOpenFiles.length > 0 ? newOpenFiles[newOpenFiles.length - 1] : null
    }

    set({ openFiles: newOpenFiles, activeFile: newActive, unsavedFiles: newUnsaved })
  },

  setActiveFile: (path) => {
    const { openFiles } = get()
    const file = openFiles.find(f => f.path === path)
    if (file) set({ activeFile: file })
  },

  updateFileContent: (path, content) => {
    const { openFiles, unsavedFiles } = get()
    const newOpenFiles = openFiles.map(f => 
      f.path === path ? { ...f, content } : f
    )
    
    const file = newOpenFiles.find(f => f.path === path)
    const newUnsaved = new Set(unsavedFiles)
    
    if (file && file.content !== file.originalContent) {
      newUnsaved.add(path)
    } else {
      newUnsaved.delete(path)
    }

    set({ openFiles: newOpenFiles, unsavedFiles: newUnsaved })
  },

  saveFile: async (path) => {
    const { openFiles, unsavedFiles } = get()
    const file = openFiles.find(f => f.path === path)
    if (!file) return

    try {
      const { activeProjectId } = get()
      await workspaceService.saveFile(path, file.content, activeProjectId)
      
      const newOpenFiles = openFiles.map(f => 
        f.path === path ? { ...f, originalContent: file.content } : f
      )
      
      const newUnsaved = new Set(unsavedFiles)
      newUnsaved.delete(path)
      
      set({ openFiles: newOpenFiles, unsavedFiles: newUnsaved })
    } catch (err) {
      console.error('Failed to save file', err)
    }
  },

  // UI state toggles
  toggleCommandPalette: () => set((s) => ({ commandPaletteOpen: !s.commandPaletteOpen })),
  toggleFileSearch: () => set((s) => ({ fileSearchOpen: !s.fileSearchOpen })),
  toggleGlobalSearch: () => set((s) => ({ globalSearchOpen: !s.globalSearchOpen })),
  toggleTerminal: () => set((s) => ({ terminalOpen: !s.terminalOpen })),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  setCommandPaletteOpen: (val) => set({ commandPaletteOpen: val }),
  setFileSearchOpen: (val) => set({ fileSearchOpen: val }),
  setGlobalSearchOpen: (val) => set({ globalSearchOpen: val }),

  addLog: (msg, type = 'info') => {
    set((s) => ({
      logs: [...s.logs, { id: Date.now() + Math.random(), msg, type, timestamp: new Date() }]
    }))
  },
  clearLogs: () => set({ logs: [] })
}))
