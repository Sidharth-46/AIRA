import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { projectService } from '../services'
import LoadingSpinner from '../components/Common/LoadingSpinner'
import { HiOutlineFolder, HiOutlineUpload, HiOutlineTrash, HiOutlineCode, HiOutlineExternalLink } from 'react-icons/hi'
import toast from 'react-hot-toast'

export default function Projects() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef(null)
  const navigate = useNavigate()

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

  const handleDelete = async (e, id) => {
    e.preventDefault()
    e.stopPropagation()
    if (!window.confirm('Are you sure you want to delete this project?')) return
    try {
      await projectService.deleteProject(id)
      setProjects(prev => prev.filter(p => p._id !== id && p.id !== id))
      toast.success('Project deleted')
    } catch (err) {
      console.error('Delete failed', err)
      toast.error('Failed to delete project')
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
                  
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ 
                      fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600,
                      padding: '4px 8px', borderRadius: '6px', 
                      background: 'var(--color-aira-surface)', color: 'var(--color-aira-text-muted)',
                    }}>
                      {project.type || 'uploaded'}
                    </span>
                    <button 
                      onClick={(e) => handleDelete(e, project._id || project.id)}
                      style={{ 
                        padding: '4px', borderRadius: '6px', background: 'transparent', border: 'none', 
                        color: 'var(--color-aira-text-dim)', cursor: 'pointer', opacity: 0, transition: 'opacity 0.1s ease',
                      }}
                      className="group-hover:opacity-100"
                      onMouseEnter={(e) => { e.currentTarget.style.opacity = '1'; e.currentTarget.style.color = '#EF4444' }}
                      onMouseLeave={(e) => { e.currentTarget.style.opacity = '0'; e.currentTarget.style.color = 'var(--color-aira-text-dim)' }}
                    >
                      <HiOutlineTrash style={{ fontSize: '14px' }} />
                    </button>
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
    </div>
  )
}
