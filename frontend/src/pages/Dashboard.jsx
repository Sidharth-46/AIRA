import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useDashboardStore } from '../stores/dashboardStore'
import { useAuthStore } from '../stores/authStore'
import { useWorkspaceStore } from '../stores/workspaceStore'
import StatCard from '../components/Dashboard/StatCard'
import UsageChart from '../components/Dashboard/UsageChart'
import { HiOutlineChat, HiOutlineFolder, HiOutlineCode, HiOutlineLightningBolt, HiOutlinePlus } from 'react-icons/hi'

export default function Dashboard() {
  const { user } = useAuthStore()
  const { stats, usage, loading, fetchDashboardData } = useDashboardStore()
  const { activeProjectId, activeProjectName, fileTree } = useWorkspaceStore()

  useEffect(() => {
    fetchDashboardData()
  }, [fetchDashboardData])

  if (loading) {
    return (
      <div style={{ padding: '48px 32px' }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div style={{ height: '120px', borderRadius: '12px' }} className="animate-pulse-skeleton" />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px' }}>
            {[1, 2, 3, 4].map(i => <div key={i} style={{ height: '140px', borderRadius: '16px' }} className="animate-pulse-skeleton" />)}
          </div>
        </div>
      </div>
    )
  }

  const displayStats = {
    totalChats: stats?.totalChats ?? 0,
    uploadedRepos: stats?.uploadedRepos ?? 0,
    generatedFiles: stats?.generatedFiles ?? 0,
    agentCalls: stats?.agentCalls ?? 0
  }

  // Calculate file count from tree recursively
  const countFiles = (nodes) => {
    let count = 0;
    for (const node of nodes) {
      if (node.type === 'file') count++;
      if (node.children) count += countFiles(node.children);
    }
    return count;
  }
  
  const totalFiles = fileTree ? countFiles(fileTree) : 0;

  const displayUsage = usage?.length > 0 ? usage : [
    { date: 'Mon', count: 12 }, { date: 'Tue', count: 18 }, { date: 'Wed', count: 5 },
    { date: 'Thu', count: 24 }, { date: 'Fri', count: 8 }, { date: 'Sat', count: 2 }, { date: 'Sun', count: 15 }
  ]

  return (
    <div style={{ padding: '48px 32px', minHeight: '100%', background: 'var(--color-aira-bg)' }}>
      <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
        
        {/* Welcome */}
        <div style={{ marginBottom: '32px' }}>
          <h1 style={{ fontSize: '36px', fontWeight: 700, color: 'var(--color-aira-text)', marginBottom: '8px' }}>
            Welcome back, {user?.username ?? 'Developer'}
          </h1>
          <p style={{ fontSize: '15px', color: 'var(--color-aira-text-dim)', lineHeight: '1.6' }}>
            Here's an overview of your workspace.
          </p>
          <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
            <Link to="/chat" className="btn-primary" style={{ textDecoration: 'none' }}>
              <HiOutlinePlus /> New Chat
            </Link>
            <Link to="/projects" className="btn-secondary" style={{ textDecoration: 'none' }}>
              <HiOutlineFolder /> Projects
            </Link>
          </div>
        </div>

        {/* Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px', marginBottom: '32px' }}>
          <StatCard title="Total Chats" value={displayStats.totalChats} icon={HiOutlineChat} color="#6366F1" />
          <StatCard title="Repositories" value={displayStats.uploadedRepos} icon={HiOutlineFolder} color="#22C55E" />
          <StatCard title="Files Generated" value={displayStats.generatedFiles} icon={HiOutlineCode} color="#6366F1" />
          <StatCard title="Agent Calls" value={displayStats.agentCalls} icon={HiOutlineLightningBolt} color="#F59E0B" />
        </div>

        {/* Charts & Activity */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
          <div className="card" style={{ padding: '24px' }}>
            <h2 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-aira-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '24px' }}>
              Activity Overview
            </h2>
            <UsageChart data={displayUsage} />
          </div>

          <div className="card" style={{ padding: '24px' }}>
            <h2 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-aira-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '24px' }}>
              Current Active Project
            </h2>
            {activeProjectId ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--color-aira-text-dim)', marginBottom: '4px' }}>Project Name</div>
                  <div style={{ fontSize: '15px', color: 'var(--color-aira-text)', fontWeight: 500 }}>
                    {activeProjectName || activeProjectId}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--color-aira-text-dim)', marginBottom: '4px' }}>Total Files</div>
                  <div style={{ fontSize: '15px', color: 'var(--color-aira-text)', fontWeight: 500 }}>{totalFiles}</div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--color-aira-text-dim)', marginBottom: '4px' }}>Status</div>
                  <div style={{ fontSize: '14px', display: 'inline-block', padding: '4px 10px', background: 'rgba(34, 197, 94, 0.1)', color: '#22c55e', borderRadius: '12px' }}>
                    Active
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '200px', color: 'var(--color-aira-text-dim)' }}>
                No active project loaded
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
