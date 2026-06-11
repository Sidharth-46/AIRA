import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { workspaceService } from '../services'

const STORAGE_KEY = 'aira_workspace_state'

export const useWorkspaceStore = create(
  persist(
    (set, get) => ({
      // ── Project State ──
      activeProjectId: null,
      activeProjectName: null,
      fileTree: [],

      // ── Editor State ──
      openFiles: [],        // Array of { path, name, type, content, originalContent }
      activeFile: null,      // Same shape as openFiles entry
      unsavedFiles: new Set(),
      cursorPosition: { line: 1, column: 1 },

      // ── Explorer State ──
      expandedFolders: [],   // Array of folder paths that are expanded

      // ── Panel State ──
      sidebarOpen: true,
      sidebarWidth: 240,
      sidebarTab: 'explorer', // 'explorer' | 'git'
      copilotOpen: false,
      copilotWidth: 380,
      previewOpen: false,
      terminalOpen: true,
      bottomPanelHeight: 200,
      bottomPanelTab: 'terminal', // 'terminal' | 'problems' | 'output'

      // ── Overlay State ──
      commandPaletteOpen: false,
      fileSearchOpen: false,
      globalSearchOpen: false,

      // ── Context Menu ──
      contextMenu: null, // { x, y, node } or null

      // ── Logs (for output tab) ──
      logs: [],
      problems: [],

      // ════════════════════════════════════════════
      //  PROJECT ACTIONS
      // ════════════════════════════════════════════

      setFileTree: (tree) => set({ fileTree: tree }),

      refreshTree: async (projectId) => {
        try {
          const res = await workspaceService.getTree(projectId)
          set({
            fileTree: res.data.tree,
            activeProjectId: projectId,
            activeProjectName: res.data.projectName || null,
          })
        } catch (err) {
          console.error('Failed to fetch tree', err)
        }
      },

      // ════════════════════════════════════════════
      //  FILE ACTIONS
      // ════════════════════════════════════════════

      openFile: async (fileNode) => {
        const { openFiles } = get()

        // Check if already open
        const existing = openFiles.find((f) => f.path === fileNode.path)
        if (existing) {
          set({ activeFile: existing })
          return
        }

        try {
          const { activeProjectId } = get()
          const res = await workspaceService.readFile(fileNode.path, activeProjectId)

          const fileData = res.data?.file || res.data?.data?.file || res.data
          const content = typeof fileData?.content === 'string' ? fileData.content : null

          const newFile = { ...fileNode, content, originalContent: content }
          set({
            openFiles: [...openFiles, newFile],
            activeFile: newFile,
          })
        } catch (err) {
          console.error(`Failed to open file: ${fileNode.path}`, err)
        }
      },

      closeFile: (path) => {
        const { openFiles, activeFile, unsavedFiles } = get()
        const newOpenFiles = openFiles.filter((f) => f.path !== path)

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
        const file = openFiles.find((f) => f.path === path)
        if (file) set({ activeFile: file })
      },

      updateFileContent: (path, content) => {
        const { openFiles, unsavedFiles } = get()
        const newOpenFiles = openFiles.map((f) => (f.path === path ? { ...f, content } : f))

        const file = newOpenFiles.find((f) => f.path === path)
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
        const file = openFiles.find((f) => f.path === path)
        if (!file) return

        try {
          const { activeProjectId } = get()
          await workspaceService.saveFile(path, file.content, activeProjectId)

          const newOpenFiles = openFiles.map((f) =>
            f.path === path ? { ...f, originalContent: file.content } : f
          )

          const newUnsaved = new Set(unsavedFiles)
          newUnsaved.delete(path)

          set({ openFiles: newOpenFiles, unsavedFiles: newUnsaved })
        } catch (err) {
          console.error('Failed to save file', err)
        }
      },

      // ── File mutations ──
      createFile: async (filePath, isDirectory = false, content = '') => {
        const { activeProjectId, refreshTree } = get()
        try {
          await workspaceService.createFile({
            path: filePath,
            is_directory: isDirectory,
            content,
            project: activeProjectId,
          })
          await refreshTree(activeProjectId)
        } catch (err) {
          console.error('Failed to create file', err)
          throw err
        }
      },

      deleteFileFromTree: async (filePath) => {
        const { activeProjectId, refreshTree, closeFile } = get()
        try {
          await workspaceService.deleteFile(filePath, activeProjectId)
          closeFile(filePath)
          await refreshTree(activeProjectId)
        } catch (err) {
          console.error('Failed to delete file', err)
          throw err
        }
      },

      renameFile: async (oldPath, newPath) => {
        const { activeProjectId, refreshTree, openFiles, activeFile } = get()
        try {
          await workspaceService.renameFile(oldPath, newPath, activeProjectId)
          // Update open tabs if the renamed file was open
          const newOpenFiles = openFiles.map((f) => {
            if (f.path === oldPath) {
              return { ...f, path: newPath, name: newPath.split('/').pop() }
            }
            return f
          })
          const newActive =
            activeFile?.path === oldPath
              ? { ...activeFile, path: newPath, name: newPath.split('/').pop() }
              : activeFile
          set({ openFiles: newOpenFiles, activeFile: newActive })
          await refreshTree(activeProjectId)
        } catch (err) {
          console.error('Failed to rename file', err)
          throw err
        }
      },

      // ════════════════════════════════════════════
      //  EXPLORER ACTIONS
      // ════════════════════════════════════════════

      toggleFolder: (folderPath) => {
        const { expandedFolders } = get()
        const isExpanded = expandedFolders.includes(folderPath)
        set({
          expandedFolders: isExpanded
            ? expandedFolders.filter((p) => p !== folderPath)
            : [...expandedFolders, folderPath],
        })
      },

      isFolderExpanded: (folderPath) => {
        return get().expandedFolders.includes(folderPath)
      },

      // ════════════════════════════════════════════
      //  PANEL ACTIONS
      // ════════════════════════════════════════════

      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
      setSidebarWidth: (w) => set({ sidebarWidth: Math.max(180, Math.min(w, 500)) }),
      setSidebarTab: (tab) => set({ sidebarTab: tab }),

      toggleCopilot: () => set((s) => ({ copilotOpen: !s.copilotOpen })),
      setCopilotWidth: (w) => set({ copilotWidth: Math.max(280, Math.min(w, 600)) }),

      togglePreview: () => set((s) => ({ previewOpen: !s.previewOpen })),

      toggleTerminal: () => set((s) => ({ terminalOpen: !s.terminalOpen })),
      setBottomPanelHeight: (h) => set({ bottomPanelHeight: Math.max(100, Math.min(h, 500)) }),
      setBottomPanelTab: (tab) => set({ bottomPanelTab: tab }),

      setCursorPosition: (line, column) => set({ cursorPosition: { line, column } }),

      // ── Overlay toggles ──
      toggleCommandPalette: () => set((s) => ({ commandPaletteOpen: !s.commandPaletteOpen })),
      toggleFileSearch: () => set((s) => ({ fileSearchOpen: !s.fileSearchOpen })),
      toggleGlobalSearch: () => set((s) => ({ globalSearchOpen: !s.globalSearchOpen })),

      setCommandPaletteOpen: (val) => set({ commandPaletteOpen: val }),
      setFileSearchOpen: (val) => set({ fileSearchOpen: val }),
      setGlobalSearchOpen: (val) => set({ globalSearchOpen: val }),

      // ── Context Menu ──
      showContextMenu: (x, y, node) => set({ contextMenu: { x, y, node } }),
      hideContextMenu: () => set({ contextMenu: null }),

      // ── Logs & Problems ──
      addLog: (msg, type = 'info') => {
        set((s) => ({
          logs: [
            ...s.logs,
            { id: Date.now() + Math.random(), msg, type, timestamp: new Date() },
          ],
        }))
      },
      clearLogs: () => set({ logs: [] }),

      addProblem: (problem) => set((s) => ({ problems: [...s.problems, problem] })),
      clearProblems: () => set({ problems: [] }),

      // ════════════════════════════════════════════
      //  REHYDRATION — restore file contents on load
      // ════════════════════════════════════════════

      rehydrateOpenFiles: async (overrideProjectId = null) => {
        const { openFiles, activeFile, activeProjectId } = get()
        const targetProjectId = overrideProjectId || activeProjectId

        if (!targetProjectId || !Array.isArray(openFiles) || openFiles.length === 0) {
          console.log('WORKSPACE_RESTORE_SKIPPED', { targetProjectId, openFilesLength: openFiles?.length })
          return
        }

        console.log('WORKSPACE_RESTORE_START', { targetProjectId, filesCount: openFiles.length })
        const rehydrated = []
        
        for (const file of openFiles) {
          if (!file || !file.path) continue

          if (file.content !== undefined && file.content !== null) {
            rehydrated.push(file)
            continue
          }
          
          try {
            const res = await workspaceService.readFile(file.path, targetProjectId)
            const fileData = res.data?.file || res.data?.data?.file || res.data
            const content = typeof fileData?.content === 'string' ? fileData.content : null
            rehydrated.push({ ...file, content, originalContent: content })
          } catch (error) {
            console.error(`WORKSPACE_RESTORE_FAILURE for file ${file.path}:`, error)
            rehydrated.push({ ...file, content: null, originalContent: null })
          }
        }

        const newActive = activeFile && activeFile.path
          ? rehydrated.find((f) => f.path === activeFile.path) || rehydrated[0] || null
          : rehydrated.length > 0 ? rehydrated[0] : null

        console.log('WORKSPACE_RESTORE_COMPLETE', { hydratedFiles: rehydrated.length, activeFilePath: newActive?.path })
        set({ openFiles: rehydrated, activeFile: newActive })
      },
    }),
    {
      name: STORAGE_KEY,
      partialize: (state) => ({
        activeProjectId: state.activeProjectId,
        activeProjectName: state.activeProjectName,
        openFiles: state.openFiles.map((f) => ({
          path: f.path,
          name: f.name,
          type: f.type,
        })),
        activeFile: state.activeFile
          ? { path: state.activeFile.path, name: state.activeFile.name, type: state.activeFile.type }
          : null,
        expandedFolders: state.expandedFolders,
        sidebarOpen: state.sidebarOpen,
        sidebarWidth: state.sidebarWidth,
        sidebarTab: state.sidebarTab,
        copilotOpen: state.copilotOpen,
        copilotWidth: state.copilotWidth,
        previewOpen: state.previewOpen,
        terminalOpen: state.terminalOpen,
        bottomPanelHeight: state.bottomPanelHeight,
        bottomPanelTab: state.bottomPanelTab,
      }),
      // Merge persisted state with defaults, converting Sets properly
      merge: (persisted, current) => ({
        ...current,
        ...persisted,
        unsavedFiles: new Set(),
        fileTree: [],
        logs: [],
        problems: [],
        contextMenu: null,
        commandPaletteOpen: false,
        fileSearchOpen: false,
        globalSearchOpen: false,
      }),
    }
  )
)
