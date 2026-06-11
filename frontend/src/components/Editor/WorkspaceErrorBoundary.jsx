import React from 'react'

export class WorkspaceErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('WORKSPACE_RENDER_ERROR:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="workspace-empty" style={{ flexDirection: 'column', gap: '16px' }}>
          <div className="workspace-empty-icon text-red-500 bg-red-500/10 mb-4">
            <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="workspace-empty-title text-aira-text">Editor failed to initialize</h2>
          <p className="workspace-empty-text text-aira-text-dim text-center max-w-md">
            Attempting recovery... {this.state.error?.message || "An unexpected error occurred while rendering the workspace."}
          </p>
          <div className="flex gap-4 mt-6">
            <button
              onClick={() => {
                localStorage.removeItem('aira_workspace_state')
                window.location.reload()
              }}
              className="btn-primary"
            >
              Clear State & Retry
            </button>
            <button
              onClick={() => {
                localStorage.removeItem('aira_workspace_state')
                window.location.href = '/projects'
              }}
              className="btn-secondary"
            >
              Return to Projects
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default WorkspaceErrorBoundary
