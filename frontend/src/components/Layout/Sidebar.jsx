import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { HiOutlineCode, HiOutlineFolderOpen, HiOutlineHome, HiOutlineLogout, HiOutlineMoon, HiOutlinePlus, HiOutlineSun, HiOutlineViewGrid, HiChevronDoubleLeft, HiChevronDoubleRight } from 'react-icons/hi'
import { useThemeStore } from '../../stores/themeStore'
import ChatList from '../Chat/ChatList'

export default function Sidebar({ isOpen, toggleSidebar }) {
  const { user, logout } = useAuthStore()
  const { theme, toggleTheme } = useThemeStore()
  const location = useLocation()

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: HiOutlineViewGrid },
    { name: 'Chat', path: '/chat', icon: HiOutlineHome },
    { name: 'Workspace', path: '/workspace', icon: HiOutlineCode },
    { name: 'Projects', path: '/projects', icon: HiOutlineFolderOpen },
  ]

  const [isCollapsed, setIsCollapsed] = useState(() => {
    return localStorage.getItem('aira_sidebar_collapsed') === 'true'
  })

  const toggleCollapse = () => {
    const nextState = !isCollapsed
    setIsCollapsed(nextState)
    localStorage.setItem('aira_sidebar_collapsed', nextState)
    console.log(`SIDEBAR_${nextState ? 'COLLAPSED' : 'EXPANDED'}`)
  }

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-40 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <aside 
        className={`fixed lg:sticky top-0 left-0 h-screen border-r transform transition-all duration-200 z-50 flex flex-col ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
        style={{ 
          width: isCollapsed ? '72px' : '240px',
          background: 'var(--color-aira-surface)', 
          borderColor: 'var(--color-aira-border)' 
        }}
      >
        {/* Logo and Collapse Toggle */}
        <div className="flex items-center justify-between border-b" style={{ height: '64px', padding: isCollapsed ? '0' : '0 16px', borderColor: 'var(--color-aira-border)', justifyContent: isCollapsed ? 'center' : 'space-between' }}>
          <div className="flex items-center gap-3" style={{ justifyContent: isCollapsed ? 'center' : 'flex-start', width: isCollapsed ? '100%' : 'auto' }}>
            <img src={theme === 'light' ? '/logo-dark.png' : '/logo.png'} alt="AIRA" style={{ width: '32px', height: '32px' }} />
            {!isCollapsed && <span className="font-semibold text-base tracking-wide" style={{ color: 'var(--color-aira-text)' }}>AIRA</span>}
          </div>
          {!isCollapsed && (
            <button onClick={toggleCollapse} className="text-aira-text-muted hover:text-aira-text transition-colors p-1 rounded-md hover:bg-aira-surface-3">
              <HiChevronDoubleLeft style={{ fontSize: '16px' }} />
            </button>
          )}
        </div>

        {/* Expand Toggle when Collapsed */}
        {isCollapsed && (
          <div className="flex justify-center" style={{ padding: '8px 0' }}>
            <button onClick={toggleCollapse} className="text-aira-text-muted hover:text-aira-text transition-colors p-2 rounded-md hover:bg-aira-surface-3">
              <HiChevronDoubleRight style={{ fontSize: '18px' }} />
            </button>
          </div>
        )}

        {/* New Chat */}
        <div style={{ padding: isCollapsed ? '8px 0' : '16px 16px 8px', display: 'flex', justifyContent: 'center' }}>
          <Link 
            to="/chat"
            className="flex items-center justify-center gap-2 btn-primary text-sm transition-all"
            style={{ height: '40px', width: isCollapsed ? '40px' : '100%', borderRadius: '10px', padding: isCollapsed ? '0' : '0 16px' }}
            onClick={() => {
              localStorage.removeItem('aira_active_chat')
              if (window.innerWidth < 1024) toggleSidebar()
            }}
            title="New Chat"
          >
            <HiOutlinePlus style={{ fontSize: '18px', flexShrink: 0 }} />
            {!isCollapsed && <span>New Chat</span>}
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto" style={{ padding: isCollapsed ? '8px' : '8px 12px' }}>
          {!isCollapsed && (
            <div className="uppercase tracking-wider font-medium" style={{ fontSize: '11px', color: 'var(--color-aira-text-dim)', padding: '8px 12px 6px', marginBottom: '2px' }}>
              Menu
            </div>
          )}
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', alignItems: isCollapsed ? 'center' : 'stretch' }}>
            {navItems.map((item) => {
              const isActive = location.pathname.startsWith(item.path)
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className="flex items-center transition-colors"
                  style={{ 
                    height: '40px', 
                    width: isCollapsed ? '40px' : '100%',
                    justifyContent: isCollapsed ? 'center' : 'flex-start',
                    gap: isCollapsed ? '0' : '12px',
                    padding: isCollapsed ? '0' : '0 12px', 
                    borderRadius: '10px',
                    fontSize: '14px',
                    fontWeight: isActive ? '500' : '400',
                    color: isActive ? 'var(--color-aira-text)' : 'var(--color-aira-text-muted)',
                    background: isActive ? 'var(--color-aira-surface-3)' : 'transparent',
                  }}
                  title={item.name}
                  onClick={() => window.innerWidth < 1024 && toggleSidebar()}
                  onMouseEnter={(e) => { if (!isActive) { e.currentTarget.style.background = 'var(--color-aira-surface-3)'; e.currentTarget.style.color = 'var(--color-aira-text)' }}}
                  onMouseLeave={(e) => { if (!isActive) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--color-aira-text-muted)' }}}
                >
                  <item.icon style={{ fontSize: '18px', color: isActive ? 'var(--color-aira-primary)' : 'inherit', flexShrink: 0 }} />
                  {!isCollapsed && <span>{item.name}</span>}
                </Link>
              )
            })}
          </div>

          {/* Recent Chats */}
          {!isCollapsed && (
            <>
              <div className="uppercase tracking-wider font-medium" style={{ fontSize: '11px', color: 'var(--color-aira-text-dim)', padding: '24px 12px 6px' }}>
                Recent Chats
              </div>
              <ChatList />
            </>
          )}
        </nav>

        {/* Bottom */}
        <div style={{ padding: isCollapsed ? '8px' : '8px 12px', borderTop: '1px solid var(--color-aira-border)', display: 'flex', flexDirection: 'column', alignItems: isCollapsed ? 'center' : 'stretch' }}>
          <button
            onClick={toggleTheme}
            className="flex items-center transition-colors"
            style={{ height: '40px', width: isCollapsed ? '40px' : '100%', justifyContent: isCollapsed ? 'center' : 'flex-start', gap: isCollapsed ? '0' : '12px', padding: isCollapsed ? '0' : '0 12px', borderRadius: '10px', fontSize: '14px', color: 'var(--color-aira-text-muted)', background: 'transparent', border: 'none', cursor: 'pointer' }}
            title={theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-aira-surface-3)' }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent' }}
          >
            {theme === 'dark' ? <HiOutlineSun style={{ fontSize: '18px', flexShrink: 0 }} /> : <HiOutlineMoon style={{ fontSize: '18px', flexShrink: 0 }} />}
            {!isCollapsed && <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>}
          </button>

          <button
            onClick={logout}
            className="flex items-center transition-colors"
            style={{ height: '40px', width: isCollapsed ? '40px' : '100%', justifyContent: isCollapsed ? 'center' : 'flex-start', gap: isCollapsed ? '0' : '12px', padding: isCollapsed ? '0' : '0 12px', borderRadius: '10px', fontSize: '14px', color: 'var(--color-aira-text-muted)', background: 'transparent', border: 'none', cursor: 'pointer' }}
            title="Sign Out"
            onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-aira-surface-3)'; e.currentTarget.style.color = '#EF4444' }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--color-aira-text-muted)' }}
          >
            <HiOutlineLogout style={{ fontSize: '18px', flexShrink: 0 }} />
            {!isCollapsed && <span>Sign Out</span>}
          </button>

          {/* User */}
          <div className="flex items-center" style={{ padding: isCollapsed ? '12px 0 8px' : '12px 8px 8px', marginTop: '4px', borderTop: '1px solid var(--color-aira-border)', justifyContent: isCollapsed ? 'center' : 'flex-start', gap: isCollapsed ? '0' : '12px' }}>
            <div className="flex items-center justify-center font-medium" 
              style={{ width: '32px', height: '32px', borderRadius: '50%', fontSize: '13px', background: 'var(--color-aira-surface-3)', border: '1px solid var(--color-aira-border)', color: 'var(--color-aira-text)', flexShrink: 0 }}
              title={user?.email}>
              {user?.username?.[0]?.toUpperCase() ?? 'U'}
            </div>
            {!isCollapsed && (
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <p className="truncate" style={{ fontSize: '14px', fontWeight: 500, color: 'var(--color-aira-text)' }}>{user?.username ?? 'User'}</p>
                <p className="truncate" style={{ fontSize: '12px', color: 'var(--color-aira-text-dim)' }}>{user?.email ?? ''}</p>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  )
}
