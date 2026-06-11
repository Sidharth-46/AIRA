import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts'

import FileExplorer from '../components/Editor/FileExplorer'
import TabBar from '../components/Editor/TabBar'
import MonacoEditor from '../components/Editor/MonacoEditor'
import BottomPanel from '../components/Editor/Terminal'
import FileSearch from '../components/Editor/FileSearch'
import GlobalSearch from '../components/Editor/GlobalSearch'
import CommandPalette from '../components/Editor/CommandPalette'
import WorkspaceToolbar from '../components/Editor/WorkspaceToolbar'
import StatusBar from '../components/Editor/StatusBar'
import CopilotPanel from '../components/Editor/CopilotPanel'
import ContextMenu from '../components/Editor/ContextMenu'
import ResizablePanel from '../components/Editor/ResizablePanel'
import LoadingSpinner from '../components/Common/LoadingSpinner'
import PreviewPanel from '../components/Editor/PreviewPanel'
import GitPanel from '../components/Editor/GitPanel'
import WorkspaceErrorBoundary from '../components/Editor/WorkspaceErrorBoundary'
import { HiOutlineFolder, HiOutlineShare } from 'react-icons/hi'

export default function Workspace() {
  const [searchParams] = useSearchParams()
  const projectId = searchParams.get('project')

  const {
    refreshTree,
    rehydrateOpenFiles,
    activeProjectId,
    sidebarOpen,
    sidebarWidth,
    setSidebarWidth,
    sidebarTab,
    setSidebarTab,
    copilotOpen,
    copilotWidth,
    setCopilotWidth,
    previewOpen,
    terminalOpen,
    bottomPanelHeight,
    setBottomPanelHeight,
    hideContextMenu,
  } = useWorkspaceStore()

  const [loading, setLoading] = useState(true)

  // Initialize keyboard shortcuts
  useKeyboardShortcuts()

  useEffect(() => {
    console.log('WORKSPACE_MOUNT', { projectId, activeProjectId })
    return () => console.log('WORKSPACE_UNMOUNT')
  }, [projectId, activeProjectId])

  // Load project on mount
  useEffect(() => {
    const loadProject = async () => {
      const effectiveProjectId = projectId || activeProjectId
      if (!effectiveProjectId) {
        setLoading(false)
        return
      }

      console.log('WORKSPACE_LOAD_START', { effectiveProjectId })
      setLoading(true)

      try {
        // Clear editor state if we're switching to a different project than what's persisted
        if (projectId && activeProjectId && projectId !== activeProjectId) {
          useWorkspaceStore.setState({ 
            openFiles: [], 
            activeFile: null, 
            expandedFolders: [], 
            unsavedFiles: new Set() 
          })
        }
        
        await refreshTree(effectiveProjectId)
        await rehydrateOpenFiles(effectiveProjectId)
        console.log('WORKSPACE_LOAD_SUCCESS', { effectiveProjectId })
      } catch (err) {
        console.error('WORKSPACE_LOAD_FAILURE', err)
      } finally {
        setLoading(false)
      }
    }
    loadProject()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId])

  // Close context menu on any click
  useEffect(() => {
    const handler = () => hideContextMenu()
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [hideContextMenu])

  if (loading) {
    return (
      <div className="workspace-loading">
        <LoadingSpinner size="lg" text="Loading workspace..." />
      </div>
    )
  }

  const effectiveProjectId = projectId || activeProjectId
  if (!effectiveProjectId && useWorkspaceStore.getState().fileTree.length === 0) {
    return (
      <div className="workspace-empty">
        <div className="workspace-empty-content">
          <div className="workspace-empty-icon text-aira-text-dim mb-4">
            <svg className="w-16 h-16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
              <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
              <polyline points="13 2 13 9 20 9" />
            </svg>
          </div>
          <h2 className="workspace-empty-title text-aira-text">No Project Opened</h2>
          <p className="workspace-empty-text text-aira-text-dim text-center">
            Go to the Projects tab to select or upload a project.
          </p>
          <button 
            onClick={() => window.location.href = '/projects'} 
            className="btn-primary mt-6"
          >
            Go to Projects
          </button>
        </div>
      </div>
    )
  }

  console.log('WORKSPACE_RENDER', { effectiveProjectId })

  return (
    <WorkspaceErrorBoundary>
      <div className="workspace-root">
      {/* Top Toolbar */}
      <WorkspaceToolbar />

      {/* Main IDE Area */}
      <div className="workspace-main">
        {/* Activity Bar */}
        <div className="w-12 bg-aira-surface-3 border-r border-aira-border flex flex-col items-center py-2 gap-4">
          <button
            className={`p-2 rounded ${sidebarTab === 'explorer' && sidebarOpen ? 'text-aira-primary' : 'text-aira-text-dim hover:text-aira-text'}`}
            onClick={() => {
              if (sidebarTab === 'explorer') useWorkspaceStore.getState().toggleSidebar()
              else {
                setSidebarTab('explorer')
                if (!sidebarOpen) useWorkspaceStore.getState().toggleSidebar()
              }
            }}
            title="Explorer"
          >
            <HiOutlineFolder className="w-6 h-6" />
          </button>
          <button
            className={`p-2 rounded ${sidebarTab === 'git' && sidebarOpen ? 'text-aira-primary' : 'text-aira-text-dim hover:text-aira-text'}`}
            onClick={() => {
              if (sidebarTab === 'git') useWorkspaceStore.getState().toggleSidebar()
              else {
                setSidebarTab('git')
                if (!sidebarOpen) useWorkspaceStore.getState().toggleSidebar()
              }
            }}
            title="Source Control"
          >
            <HiOutlineShare className="w-6 h-6" />
          </button>
        </div>

        {/* Left Sidebar: File Explorer or Git */}
        {sidebarOpen && (
          <ResizablePanel
            direction="horizontal"
            size={sidebarWidth}
            onResize={setSidebarWidth}
            minSize={180}
            maxSize={500}
            side="right"
          >
            {sidebarTab === 'explorer' ? <FileExplorer /> : <GitPanel />}
          </ResizablePanel>
        )}

        {/* Center: Editor + Bottom Panel */}
        <div className="workspace-center">
          {/* Tab Bar + Editor + Preview */}
          <div className="workspace-editor-area" style={{ flexDirection: 'row' }}>
            <div className="flex-1 flex flex-col min-w-0 relative">
              <TabBar />
              <div className="workspace-editor-container">
                <MonacoEditor />
              </div>
            </div>

            {previewOpen && (
              <ResizablePanel
                direction="horizontal"
                size={500}
                onResize={() => {}}
                minSize={300}
                maxSize={1000}
                side="left"
              >
                <PreviewPanel />
              </ResizablePanel>
            )}
          </div>

          {/* Bottom Panel */}
          {terminalOpen && (
            <ResizablePanel
              direction="vertical"
              size={bottomPanelHeight}
              onResize={setBottomPanelHeight}
              minSize={100}
              maxSize={500}
              side="top"
            >
              <BottomPanel />
            </ResizablePanel>
          )}
        </div>

        {/* Right: AIRA Copilot */}
        {copilotOpen && (
          <ResizablePanel
            direction="horizontal"
            size={copilotWidth}
            onResize={setCopilotWidth}
            minSize={280}
            maxSize={600}
            side="left"
          >
            <CopilotPanel />
          </ResizablePanel>
        )}
      </div>

      {/* Status Bar */}
      <StatusBar />

      {/* Overlays */}
      <FileSearch />
      <GlobalSearch />
      <CommandPalette />
      <ContextMenu />
    </div>
    </WorkspaceErrorBoundary>
  )
}
