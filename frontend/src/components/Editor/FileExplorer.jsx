import {
  HiOutlineChevronRight,
  HiOutlineChevronDown,
  HiOutlineDocument,
  HiOutlineFolder,
  HiOutlineFolderOpen,
  HiOutlineDocumentAdd,
  HiOutlineFolderAdd,
  HiOutlineRefresh,
} from 'react-icons/hi'
import { useWorkspaceStore } from '../../stores/workspaceStore'

/* ── File Icon by Extension ── */
const FILE_ICONS = {
  js: '🟨', jsx: '⚛️', ts: '🔷', tsx: '⚛️',
  py: '🐍', json: '📋', md: '📝', css: '🎨', scss: '🎨',
  html: '🌐', yaml: '⚙️', yml: '⚙️', sh: '🖥️',
  java: '☕', go: '🐹', rs: '🦀', rb: '💎', php: '🐘',
  sql: '🗄️', dockerfile: '🐳', toml: '⚙️', xml: '📄',
  svg: '🖼️', png: '🖼️', jpg: '🖼️', gif: '🖼️',
  txt: '📄', env: '🔐', gitignore: '🚫', lock: '🔒',
}

const getFileIcon = (name) => {
  const ext = name.split('.').pop()?.toLowerCase()
  return FILE_ICONS[ext] || null
}

/* ── Tree Node ── */
const FileTreeNode = ({ node, level = 0 }) => {
  const {
    openFile,
    activeFile,
    openFiles,
    expandedFolders,
    toggleFolder,
    showContextMenu,
  } = useWorkspaceStore()

  const isDir = node.type === 'directory'
  const isActive = activeFile?.path === node.path
  const isOpen = expandedFolders.includes(node.path)

  const handleClick = (e) => {
    e.stopPropagation()
    if (isDir) {
      toggleFolder(node.path)
    } else {
      openFile(node)
    }
  }

  const handleContextMenu = (e) => {
    e.preventDefault()
    e.stopPropagation()
    showContextMenu(e.clientX, e.clientY, node)
  }

  const fileIcon = !isDir ? getFileIcon(node.name) : null

  return (
    <div>
      <div
        className={`explorer-node ${isActive ? 'explorer-node-active' : ''}`}
        style={{ paddingLeft: `${level * 12 + 8}px` }}
        onClick={handleClick}
        onContextMenu={handleContextMenu}
      >
        {/* Chevron */}
        <span className="explorer-node-chevron">
          {isDir ? (
            isOpen ? (
              <HiOutlineChevronDown className="w-3 h-3" />
            ) : (
              <HiOutlineChevronRight className="w-3 h-3" />
            )
          ) : null}
        </span>

        {/* Icon */}
        <span className="explorer-node-icon">
          {isDir ? (
            isOpen ? (
              <HiOutlineFolderOpen className="text-aira-accent-2" />
            ) : (
              <HiOutlineFolder className="text-aira-accent-2" />
            )
          ) : fileIcon ? (
            <span className="text-xs">{fileIcon}</span>
          ) : (
            <HiOutlineDocument className="text-aira-text-dim" />
          )}
        </span>

        {/* Name */}
        <span className="truncate">{node.name}</span>
      </div>

      {/* Children */}
      {isDir && isOpen && node.children && (
        <div>
          {[...node.children]
            .sort((a, b) => {
              if (a.type === b.type) return a.name.localeCompare(b.name)
              return a.type === 'directory' ? -1 : 1
            })
            .map((child) => (
              <FileTreeNode key={child.path} node={child} level={level + 1} />
            ))}
        </div>
      )}
    </div>
  )
}

/* ── Main Explorer ── */
export default function FileExplorer() {
  const {
    fileTree,
    sidebarOpen,
    openFiles,
    activeFile,
    setActiveFile,
    closeFile,
    unsavedFiles,
    activeProjectId,
    refreshTree,
  } = useWorkspaceStore()

  if (!sidebarOpen) return null

  return (
    <div className="explorer-panel">
      {/* Open Editors Section */}
      {openFiles.length > 0 && (
        <div className="explorer-section">
          <div className="explorer-section-header">
            <span>OPEN EDITORS</span>
          </div>
          <div className="explorer-open-editors">
            {openFiles.map((file) => (
              <div
                key={file.path}
                className={`explorer-node ${activeFile?.path === file.path ? 'explorer-node-active' : ''}`}
                style={{ paddingLeft: '12px' }}
                onClick={() => setActiveFile(file.path)}
              >
                <span className="explorer-node-icon">
                  {unsavedFiles.has(file.path) ? (
                    <span className="w-2 h-2 rounded-full bg-aira-accent inline-block" />
                  ) : (
                    <HiOutlineDocument className="text-aira-text-dim" />
                  )}
                </span>
                <span className="truncate flex-1 text-xs">{file.name}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    closeFile(file.path)
                  }}
                  className="explorer-close-btn"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* File Tree Section */}
      <div className="explorer-section explorer-section-grow">
        <div className="explorer-section-header">
          <span>EXPLORER</span>
          <div className="explorer-section-actions">
            <button
              onClick={() => activeProjectId && refreshTree(activeProjectId)}
              className="explorer-action-btn"
              title="Refresh"
            >
              <HiOutlineRefresh className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
        <div className="explorer-tree">
          {fileTree.length > 0 ? (
            fileTree.map((node) => <FileTreeNode key={node.path} node={node} />)
          ) : (
            <div className="explorer-empty">No folder opened</div>
          )}
        </div>
      </div>
    </div>
  )
}
