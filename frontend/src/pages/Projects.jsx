import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { projectService } from '../services'
import LoadingSpinner from '../components/Common/LoadingSpinner'
import { HiOutlineFolder, HiOutlineUpload, HiOutlineTrash, HiOutlineCode, HiOutlineExternalLink, HiDotsVertical, HiOutlinePencil } from 'react-icons/hi'
import toast from 'react-hot-toast'
import { useWorkspaceStore } from '../stores/workspaceStore'

export default function Projects() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [menuOpenId, setMenuOpenId] = useState(null)
  const [projectToDelete, setProjectToDelete] = useState(null)
  
  const fileInputRef = useRef(null)
  const navigate = useNavigate()
  
  // Close menu when clicking outside
  useEffect(() => {
    const handleClick = () => setMenuOpenId(null)
    window.addEventListener('click', handleClick)
    return () => window.removeEventListener('click', handleClick)
  }, [])

  useEffect(() => {
    fetchProjects()
  }, [])

  const fetchProjects = async () => {
    try {
      setLoading(true)
      const res = await projectService.getProjects()
      setProjects(res.data.projects || [])
    } catch (err) {
      console.error('Failed to fetch projects', err)
      toast.error('Failed to load projects')
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    if (!file.name.endsWith('.zip')) { toast.error('Only ZIP files are supported'); return }

    try {
      setUploading(true)
      const loadingToast = toast.loading('Uploading and extracting project...')
      const res = await projectService.uploadProject(file)
      toast.success('Project uploaded successfully!', { id: loadingToast })
      setProjects(prev => [res.data.project, ...prev])
      if (fileInputRef.current) fileInputRef.current.value = ''
    } catch (err) {
      console.error('Upload failed', err)
      toast.error(err.response?.data?.error || 'Failed to upload project')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (id) => {
    try {
      await projectService.deleteProject(id)
      setProjects(prev => prev.filter(p => p._id !== id && p.id !== id))
      
      // If the deleted project is currently active, clear the workspace
      const { activeProjectId, exitWorkspace } = useWorkspaceStore.getState()
      if (activeProjectId === id) {
        exitWorkspace()
      }
      
      toast.success('Project deleted')
    } catch (err) {
      console.error('Delete failed', err)
      toast.error('Failed to delete project')
    } finally {
      setProjectToDelete(null)
    }
  }

  const openWorkspace = (projectId) => {
    navigate(`/workspace?project=${projectId}`)
  }

  return (
    <div style={{ padding: '48px 32px', minHeight: '100%', background: 'var(--color-aira-bg)' }}>
      <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
        
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px' }}>
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--color-aira-text)', marginBottom: '4px' }}>Projects</h1>
            <p style={{ fontSize: '14px', color: 'var(--color-aira-text-dim)' }}>Manage your uploaded repositories</p>
          </div>
          
          <div>
            <input type="file" accept=".zip" className="hidden" ref={fileInputRef} onChange={handleFileUpload} style={{ display: 'none' }} />
            <button 
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="btn-primary"
            >
              {uploading ? (
                <div style={{ width: '16px', height: '16px', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
              ) : (
                <HiOutlineUpload style={{ fontSize: '16px' }} />
              )}
              {uploading ? 'Uploading...' : 'Upload Repository'}
            </button>
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '80px 0' }}>
            <LoadingSpinner text="Loading projects..." />
          </div>
        ) : projects.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', maxWidth: '480px', margin: '64px auto 0', padding: '48px 32px' }}>
            <div style={{ 
              width: '64px', height: '64px', borderRadius: '16px', 
              background: 'var(--color-aira-surface)', border: '1px solid var(--color-aira-border)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px',
            }}>
              <HiOutlineFolder style={{ fontSize: '24px', color: 'var(--color-aira-text-dim)' }} />
            </div>
            <h2 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--color-aira-text)', marginBottom: '8px' }}>No projects yet</h2>
            <p style={{ fontSize: '14px', color: 'var(--color-aira-text-dim)', marginBottom: '24px', lineHeight: '1.6' }}>
              Upload a ZIP file of a repository or ask AIRA to generate a new project.
            </p>
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="btn-secondary"
            >
              Upload .ZIP
            </button>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
            {projects.map(project => (
              <div 
                key={project._id || project.id} 
                className="card"
                style={{ padding: '24px', cursor: 'pointer', transition: 'border-color 0.15s ease' }}
                onClick={() => openWorkspace(project._id || project.id)}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--color-aira-border-light)' }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--color-aira-border)' }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '16px' }}>
                  <div style={{ 
                    width: '40px', height: '40px', borderRadius: '10px', 
                    background: 'var(--color-aira-surface)', border: '1px solid var(--color-aira-border)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <HiOutlineCode style={{ fontSize: '18px', color: 'var(--color-aira-text-muted)' }} />
                  </div>
                  
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', position: 'relative' }}>
                    <span style={{ 
                      fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600,
                      padding: '4px 8px', borderRadius: '6px', 
                      background: 'var(--color-aira-surface)', color: 'var(--color-aira-text-muted)',
                    }}>
                      {project.type || 'uploaded'}
                    </span>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation()
                        setMenuOpenId(menuOpenId === (project._id || project.id) ? null : (project._id || project.id))
                      }}
                      style={{ 
                        padding: '4px', borderRadius: '6px', background: 'transparent', border: 'none', 
                        color: 'var(--color-aira-text-dim)', cursor: 'pointer', transition: 'all 0.15s ease',
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--color-aira-text)' }}
                      onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--color-aira-text-dim)' }}
                    >
                      <HiDotsVertical style={{ fontSize: '16px' }} />
                    </button>

                    {menuOpenId === (project._id || project.id) && (
                      <div 
                        style={{
                          position: 'absolute', top: '100%', right: 0, marginTop: '8px',
                          background: 'var(--color-aira-surface-2)', border: '1px solid var(--color-aira-border)',
                          borderRadius: '12px', padding: '6px', minWidth: '160px', zIndex: 10,
                          boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
                        }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button 
                          className="w-full text-left px-3 py-2 text-sm text-aira-text hover:bg-aira-surface rounded-md flex items-center gap-2"
                          onClick={() => { setMenuOpenId(null); openWorkspace(project._id || project.id); }}
                        >
                          <HiOutlineExternalLink /> Open Project
                        </button>
                        <button 
                          className="w-full text-left px-3 py-2 text-sm text-aira-text hover:bg-aira-surface rounded-md flex items-center gap-2"
                          onClick={() => { setMenuOpenId(null); toast('Rename coming soon!', { icon: '🚧' }) }}
                        >
                          <HiOutlinePencil /> Rename Project
                        </button>
                        <div style={{ height: '1px', background: 'var(--color-aira-border)', margin: '4px 0' }} />
                        <button 
                          className="w-full text-left px-3 py-2 text-sm text-red-500 hover:bg-red-500/10 rounded-md flex items-center gap-2"
                          onClick={() => { setMenuOpenId(null); setProjectToDelete(project) }}
                        >
                          <HiOutlineTrash /> Delete Project
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--color-aira-text)', marginBottom: '4px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {project.name}
                </h3>
                
                <p style={{ fontSize: '13px', color: 'var(--color-aira-text-dim)', marginBottom: '16px' }}>
                  {new Date(project.created_at || Date.now()).toLocaleDateString()}
                </p>
                
                {project.languages && project.languages.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '16px' }}>
                    {project.languages.slice(0, 3).map(lang => (
                      <span key={lang} style={{ 
                        fontSize: '11px', padding: '2px 8px', borderRadius: '6px',
                        background: 'var(--color-aira-surface)', color: 'var(--color-aira-text-dim)', 
                        border: '1px solid var(--color-aira-border)',
                      }}>
                        {lang}
                      </span>
                    ))}
                    {project.languages.length > 3 && (
                      <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '6px', background: 'var(--color-aira-surface)', color: 'var(--color-aira-text-dim)', border: '1px solid var(--color-aira-border)' }}>
                        +{project.languages.length - 3}
                      </span>
                    )}
                  </div>
                )}
                
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', fontWeight: 500, color: 'var(--color-aira-primary)' }}>
                  <HiOutlineExternalLink /> Open in Workspace
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {projectToDelete && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50,
          padding: '24px'
        }}>
          <div style={{
            background: 'var(--color-aira-surface)', border: '1px solid var(--color-aira-border)',
            borderRadius: '16px', padding: '32px', width: '100%', maxWidth: '420px',
            boxShadow: '0 10px 40px rgba(0,0,0,0.4)',
          }}>
            <h2 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--color-aira-text)', marginBottom: '16px' }}>
              Delete Project?
            </h2>
            <p style={{ fontSize: '15px', color: 'var(--color-aira-text-dim)', marginBottom: '16px', lineHeight: '1.5' }}>
              This will permanently delete <strong>{projectToDelete.name}</strong> and:
            </p>
            <ul style={{ 
              listStyleType: 'disc', paddingLeft: '24px', 
              color: 'var(--color-aira-text-dim)', fontSize: '14px', marginBottom: '24px',
              display: 'flex', flexDirection: 'column', gap: '8px'
            }}>
              <li>Project record</li>
              <li>Uploaded files</li>
              <li>Workspace cache</li>
              <li>Workspace chat history</li>
            </ul>
            <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '8px', marginBottom: '24px' }}>
              <p style={{ color: '#EF4444', fontSize: '13px', fontWeight: 500 }}>
                This action cannot be undone.
              </p>
            </div>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button 
                onClick={() => setProjectToDelete(null)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button 
                onClick={() => handleDelete(projectToDelete._id || projectToDelete.id)}
                className="btn-primary"
                style={{ background: '#EF4444', color: '#fff' }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
