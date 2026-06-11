import { useState, useEffect } from 'react'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { gitService } from '../../services'
import {
  HiOutlineCheck,
  HiOutlinePlus,
  HiOutlineMinus,
  HiOutlineCloudUpload,
  HiOutlineCloudDownload,
  HiOutlineRefresh,
} from 'react-icons/hi'

export default function GitPanel() {
  const { activeProjectId } = useWorkspaceStore()
  const [gitStatus, setGitStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [commitMsg, setCommitMsg] = useState('')

  const fetchStatus = async () => {
    if (!activeProjectId) return
    setLoading(true)
    try {
      const res = await gitService.getStatus(activeProjectId)
      setGitStatus(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    // Poll every 30 seconds or trigger manually
    const interval = setInterval(fetchStatus, 30000)
    return () => clearInterval(interval)
  }, [activeProjectId])

  const handleStage = async (path) => {
    try {
      await gitService.stage([path], activeProjectId)
      fetchStatus()
    } catch (err) {
      console.error(err)
    }
  }

  const handleUnstage = async (path) => {
    try {
      await gitService.unstage([path], activeProjectId)
      fetchStatus()
    } catch (err) {
      console.error(err)
    }
  }

  const handleCommit = async (e) => {
    e.preventDefault()
    if (!commitMsg.trim()) return
    try {
      await gitService.commit(commitMsg, activeProjectId)
      setCommitMsg('')
      fetchStatus()
    } catch (err) {
      alert('Commit failed: ' + err.response?.data?.error)
    }
  }

  const handlePush = async () => {
    try {
      await gitService.push(activeProjectId)
      alert('Pushed successfully')
    } catch (err) {
      alert('Push failed: ' + err.response?.data?.error)
    }
  }

  const handlePull = async () => {
    try {
      await gitService.pull(activeProjectId)
      alert('Pulled successfully')
      fetchStatus()
    } catch (err) {
      alert('Pull failed: ' + err.response?.data?.error)
    }
  }

  if (!gitStatus || !gitStatus.is_git) {
    return (
      <div className="explorer-panel p-4 text-center text-sm text-aira-text-dim">
        <p>This workspace is not a Git repository.</p>
      </div>
    )
  }

  const stagedFiles = gitStatus.files.filter((f) => f.status[0] !== ' ' && f.status[0] !== '?')
  const changedFiles = gitStatus.files.filter((f) => f.status[1] !== ' ' || f.status === '??')

  return (
    <div className="explorer-panel">
      {/* Header */}
      <div className="explorer-section-header">
        <span>SOURCE CONTROL: {gitStatus.branch}</span>
        <div className="explorer-section-actions">
          <button onClick={fetchStatus} className="explorer-action-btn" title="Refresh">
            <HiOutlineRefresh className="w-4 h-4" />
          </button>
          <button onClick={handlePull} className="explorer-action-btn" title="Pull">
            <HiOutlineCloudDownload className="w-4 h-4" />
          </button>
          <button onClick={handlePush} className="explorer-action-btn" title="Push">
            <HiOutlineCloudUpload className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Commit Box */}
      <div className="p-3 border-b border-aira-border">
        <form onSubmit={handleCommit}>
          <textarea
            value={commitMsg}
            onChange={(e) => setCommitMsg(e.target.value)}
            placeholder="Message (Enter to commit)"
            className="w-full bg-aira-surface border border-aira-border rounded p-2 text-sm text-aira-text resize-none h-20 mb-2 focus:border-aira-primary outline-none"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleCommit(e)
              }
            }}
          />
          <button
            type="submit"
            disabled={!commitMsg.trim() || stagedFiles.length === 0}
            className="w-full bg-aira-primary text-white rounded py-1.5 text-sm disabled:opacity-50"
          >
            Commit
          </button>
        </form>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Staged Changes */}
        {stagedFiles.length > 0 && (
          <div className="explorer-section">
            <div className="explorer-section-header">
              <span>STAGED CHANGES</span>
              <span className="text-xs bg-aira-surface-3 px-1.5 rounded">{stagedFiles.length}</span>
            </div>
            {stagedFiles.map((file) => (
              <div key={file.path} className="flex items-center justify-between px-3 py-1 hover:bg-aira-surface-3 group text-sm">
                <span className="truncate text-aira-text-muted">{file.path}</span>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100">
                  <button onClick={() => handleUnstage(file.path)} className="text-aira-text-dim hover:text-aira-text">
                    <HiOutlineMinus className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Changes */}
        {changedFiles.length > 0 && (
          <div className="explorer-section mt-2">
            <div className="explorer-section-header">
              <span>CHANGES</span>
              <span className="text-xs bg-aira-surface-3 px-1.5 rounded">{changedFiles.length}</span>
            </div>
            {changedFiles.map((file) => (
              <div key={file.path} className="flex items-center justify-between px-3 py-1 hover:bg-aira-surface-3 group text-sm">
                <div className="flex items-center gap-2 truncate">
                  <span className={`text-[10px] w-4 text-center font-bold ${file.status.includes('?') ? 'text-aira-success' : 'text-aira-warning'}`}>
                    {file.status[1] !== ' ' ? file.status[1] : file.status[0]}
                  </span>
                  <span className="truncate text-aira-text-muted">{file.path}</span>
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100">
                  <button onClick={() => handleStage(file.path)} className="text-aira-text-dim hover:text-aira-text">
                    <HiOutlinePlus className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
