import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useWorkspaceStore } from '../stores/workspaceStore'
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts'

import FileExplorer from '../components/Editor/FileExplorer'
import TabBar from '../components/Editor/TabBar'
import MonacoEditor from '../components/Editor/MonacoEditor'
import Terminal from '../components/Editor/Terminal'
import FileSearch from '../components/Editor/FileSearch'
import GlobalSearch from '../components/Editor/GlobalSearch'
import CommandPalette from '../components/Editor/CommandPalette'
import { projectService } from '../services'
import LoadingSpinner from '../components/Common/LoadingSpinner'

export default function Workspace() {
  const [searchParams] = useSearchParams()
  const projectId = searchParams.get('project')
  
  const { refreshTree } = useWorkspaceStore()
  const [loading, setLoading] = useState(true)

  // Initialize keyboard shortcuts
  useKeyboardShortcuts()

  useEffect(() => {
    if (projectId) {
      setLoading(true)
      // We would ideally fetch the tree dynamically. For MVP we're mocking project data or fetching.
      refreshTree(projectId).finally(() => setLoading(false))
    } else {
      // For MVP without project selection, we could show a welcome screen
      setLoading(false)
    }
  }, [projectId, refreshTree])

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading workspace..." />
      </div>
    )
  }

  if (!projectId && useWorkspaceStore.getState().fileTree.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-aira-surface text-center">
        <div>
          <div className="text-4xl mb-4 text-aira-text-dim">📁</div>
          <h2 className="text-xl font-semibold mb-2 text-aira-text">No Project Opened</h2>
          <p className="text-aira-text-dim mb-4">Go to the Projects tab to select or upload a project.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col overflow-hidden bg-aira-bg text-aira-text">
      {/* Main split view */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar: File Explorer */}
        <FileExplorer />

        {/* Center: Editor Area */}
        <div className="flex-1 flex flex-col min-w-0">
          <TabBar />
          
          <div className="flex-1 relative">
            <MonacoEditor />
          </div>

          <Terminal />
        </div>
      </div>

      {/* Overlays */}
      <FileSearch />
      <GlobalSearch />
      <CommandPalette />
    </div>
  )
}
