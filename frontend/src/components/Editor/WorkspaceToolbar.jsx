import { useWorkspaceStore } from '../../stores/workspaceStore'
import { useNavigate } from 'react-router-dom'
import {
  HiOutlinePlay,
  HiOutlineEye,
  HiOutlineSearch,
  HiOutlineTerminal,
  HiOutlineChevronLeft,
  HiOutlineChat,
  HiOutlineMenu,
  HiOutlineSave,
} from 'react-icons/hi'
import RunButton from './RunButton'

export default function WorkspaceToolbar() {
  const {
    activeProjectName,
    activeFile,
    sidebarOpen,
    copilotOpen,
    toggleSidebar,
    toggleCopilot,
    toggleTerminal,
    toggleGlobalSearch,
    saveFile,
    unsavedFiles,
  } = useWorkspaceStore()

  const navigate = useNavigate()

  const breadcrumb = activeFile?.path?.split('/') || []

  return (
    <div className="workspace-toolbar">
      {/* Left section */}
      <div className="workspace-toolbar-section">
        <button
          className="workspace-toolbar-btn"
          onClick={toggleSidebar}
          title={sidebarOpen ? 'Hide Explorer' : 'Show Explorer'}
        >
          <HiOutlineMenu className="w-4 h-4" />
        </button>

        <button
          className="workspace-toolbar-btn"
          onClick={() => navigate('/projects')}
          title="Back to Projects"
        >
          <HiOutlineChevronLeft className="w-4 h-4" />
        </button>

        <div className="workspace-toolbar-project">
          <span className="workspace-toolbar-project-name">
            {activeProjectName || 'AIRA Workspace'}
          </span>
        </div>

        {/* Breadcrumb */}
        {breadcrumb.length > 0 && (
          <div className="workspace-toolbar-breadcrumb">
            <span className="workspace-toolbar-separator">›</span>
            {breadcrumb.map((part, i) => (
              <span key={i}>
                <span className={i === breadcrumb.length - 1 ? 'text-aira-text' : 'text-aira-text-dim'}>
                  {part}
                </span>
                {i < breadcrumb.length - 1 && (
                  <span className="workspace-toolbar-separator">›</span>
                )}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Right section */}
      <div className="workspace-toolbar-section">
        <button
          className={`workspace-toolbar-btn ${useWorkspaceStore.getState().previewOpen ? 'text-aira-primary' : ''}`}
          onClick={useWorkspaceStore.getState().togglePreview}
          title="Toggle Preview"
        >
          <HiOutlineEye className="w-4 h-4" />
        </button>

        <RunButton />

        {activeFile && unsavedFiles.has(activeFile.path) && (
          <button
            className="workspace-toolbar-btn"
            onClick={() => saveFile(activeFile.path)}
            title="Save (Ctrl+S)"
          >
            <HiOutlineSave className="w-4 h-4" />
          </button>
        )}

        <button className="workspace-toolbar-btn" onClick={toggleGlobalSearch} title="Search (Ctrl+Shift+F)">
          <HiOutlineSearch className="w-4 h-4" />
        </button>

        <button className="workspace-toolbar-btn" onClick={toggleTerminal} title="Terminal (Ctrl+`)">
          <HiOutlineTerminal className="w-4 h-4" />
        </button>

        <button
          className={`workspace-toolbar-btn ${copilotOpen ? 'workspace-toolbar-btn-active' : ''}`}
          onClick={toggleCopilot}
          title="AIRA Copilot"
        >
          <HiOutlineChat className="w-4 h-4" />
          <span className="hidden sm:inline text-xs">Copilot</span>
        </button>
      </div>
    </div>
  )
}
