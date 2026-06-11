import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'

export default function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const isChatPage = location.pathname.startsWith('/chat')
  const isWorkspacePage = location.pathname.startsWith('/workspace')

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen)

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--color-aira-bg)' }}>
      {!isWorkspacePage && <Sidebar isOpen={sidebarOpen} toggleSidebar={toggleSidebar} />}

      <div className="flex-1 flex flex-col w-full min-w-0">
        {!isChatPage && !isWorkspacePage && <Header toggleSidebar={toggleSidebar} />}
        
        <main className="flex-1 overflow-auto relative">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
