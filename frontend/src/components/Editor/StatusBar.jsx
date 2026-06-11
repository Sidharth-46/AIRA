import { useWorkspaceStore } from '../../stores/workspaceStore'
import { useState, useEffect } from 'react'
import { gitService } from '../../services'

export default function StatusBar() {
  const { activeFile, cursorPosition, unsavedFiles, activeProjectId } = useWorkspaceStore()
  const [branch, setBranch] = useState('main')

  useEffect(() => {
    if (!activeProjectId) return
    let isMounted = true
    const fetchBranch = async () => {
      try {
        const res = await gitService.getStatus(activeProjectId)
        if (isMounted && res.data && res.data.is_git && res.data.branch) {
          setBranch(res.data.branch)
        }
      } catch (err) {
        // ignore
      }
    }
    fetchBranch()
    const intv = setInterval(fetchBranch, 15000)
    return () => {
      isMounted = false
      clearInterval(intv)
    }
  }, [activeProjectId])

  const getLanguage = (filename) => {
    if (!filename) return 'Plain Text'
    const ext = filename.split('.').pop()?.toLowerCase()
    const map = {
      js: 'JavaScript', jsx: 'JavaScript (React)', ts: 'TypeScript', tsx: 'TypeScript (React)',
      py: 'Python', json: 'JSON', md: 'Markdown', css: 'CSS', scss: 'SCSS',
      html: 'HTML', yaml: 'YAML', yml: 'YAML', sh: 'Shell', bash: 'Shell',
      java: 'Java', c: 'C', cpp: 'C++', h: 'C Header', hpp: 'C++ Header',
      cs: 'C#', go: 'Go', rs: 'Rust', rb: 'Ruby', php: 'PHP',
      swift: 'Swift', kt: 'Kotlin', scala: 'Scala', r: 'R', sql: 'SQL',
      xml: 'XML', toml: 'TOML', ini: 'INI', vue: 'Vue', svelte: 'Svelte',
      dart: 'Dart', dockerfile: 'Dockerfile',
    }
    return map[ext] || 'Plain Text'
  }

  return (
    <div className="workspace-statusbar">
      {/* Left */}
      <div className="workspace-statusbar-section">
        {activeProjectId && (
          <span className="workspace-statusbar-item workspace-statusbar-branch">
            <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="currentColor">
              <path d="M9.5 3.25a2.25 2.25 0 1 1 3 2.122V6A2.5 2.5 0 0 1 10 8.5H6a1 1 0 0 0-1 1v1.128a2.251 2.251 0 1 1-1.5 0V5.372a2.25 2.25 0 1 1 1.5 0v1.836A2.492 2.492 0 0 1 6 7h4a1 1 0 0 0 1-1v-.628A2.25 2.25 0 0 1 9.5 3.25Z" />
            </svg>
            {branch}
          </span>
        )}
      </div>

      {/* Right */}
      <div className="workspace-statusbar-section">
        {activeFile && (
          <>
            <span className="workspace-statusbar-item">
              Ln {cursorPosition.line}, Col {cursorPosition.column}
            </span>
            <span className="workspace-statusbar-item">UTF-8</span>
            <span className="workspace-statusbar-item">{getLanguage(activeFile.name)}</span>
            {unsavedFiles.has(activeFile.path) && (
              <span className="workspace-statusbar-item workspace-statusbar-unsaved">● Modified</span>
            )}
          </>
        )}
      </div>
    </div>
  )
}
