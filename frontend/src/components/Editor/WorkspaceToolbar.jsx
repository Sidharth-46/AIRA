import { useWorkspaceStore } from '../../stores/workspaceStore'
import { useNavigate } from 'react-router-dom'
import {
  HiOutlineSearch,
  HiOutlineTerminal,
  HiOutlineChat,
  HiOutlineMenu,
} from 'react-icons/hi'
import { HiOutlineBugAnt } from 'react-icons/hi2'
import RunButton from './RunButton'
import { toast } from 'react-hot-toast'

export default function WorkspaceToolbar() {
  const {
    activeProjectName,
    sidebarOpen,
    copilotOpen,
    toggleSidebar,
    toggleCopilot,
    toggleTerminal,
    toggleGlobalSearch,
  } = useWorkspaceStore()

  const navigate = useNavigate()

  return (
    <div className="workspace-toolbar">
      {/* Left section: Project Name */}
      <div className="workspace-toolbar-section">
        <div className="workspace-toolbar-project">
          {activeProjectName || 'AIRA Workspace'}
        </div>
      </div>

      {/* Center section: Primary Actions */}
      <div className="workspace-toolbar-section flex-1 justify-center gap-1 sm:gap-2">
        <button
          className="workspace-toolbar-btn"
          onClick={toggleSidebar}
          title={sidebarOpen ? 'Hide Explorer' : 'Show Explorer'}
        >
          <HiOutlineMenu className="w-[18px] h-[18px]" />
          <span className="hidden md:inline">Explorer</span>
        </button>

        <button 
          className="workspace-toolbar-btn" 
          onClick={toggleGlobalSearch} 
          title="Search (Ctrl+Shift+F)"
        >
          <HiOutlineSearch className="w-[18px] h-[18px]" />
          <span className="hidden md:inline">Search</span>
        </button>

        <RunButton />

        <button 
          className="workspace-toolbar-btn" 
          onClick={() => toast('Debugger coming soon!', { icon: '🚧' })} 
          title="Debug Project"
        >
          <HiOutlineBugAnt className="w-[18px] h-[18px]" />
          <span className="hidden md:inline">Debug</span>
        </button>

        <button 
          className="workspace-toolbar-btn" 
          onClick={toggleTerminal} 
          title="Terminal (Ctrl+`)"
        >
          <HiOutlineTerminal className="w-[18px] h-[18px]" />
          <span className="hidden md:inline">Terminal</span>
        </button>
      </div>

      {/* Right section: System Actions */}
      <div className="workspace-toolbar-section">
        <button
          className={`workspace-toolbar-btn ${copilotOpen ? 'workspace-toolbar-btn-active' : ''}`}
          onClick={toggleCopilot}
          title="AIRA Copilot"
        >
          <HiOutlineChat className="w-[18px] h-[18px]" />
          <span className="hidden sm:inline">
            {copilotOpen ? 'AIRA Copilot' : 'Open Copilot'}
          </span>
        </button>

        <button
          className="workspace-toolbar-btn workspace-toolbar-btn-bordered text-red-500 hover:text-red-400 hover:bg-red-500/10 hover:border-red-500/30"
          onClick={() => {
            useWorkspaceStore.getState().exitWorkspace()
            navigate('/projects')
          }}
          title="Exit Workspace"
        >
          <span className="hidden sm:inline text-xs font-medium">Exit Workspace</span>
          <span className="sm:hidden text-xs font-medium">Exit</span>
        </button>
      </div>
    </div>
  )
}
