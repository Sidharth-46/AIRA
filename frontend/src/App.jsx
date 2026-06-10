import { useEffect, useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import MainLayout from './components/Layout/MainLayout'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Chat from './pages/Chat'
import Dashboard from './pages/Dashboard'
import Workspace from './pages/Workspace'
import Projects from './pages/Projects'

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  const { checkAuth } = useAuthStore()
  const [isInitializing, setIsInitializing] = useState(true)

  useEffect(() => {
    checkAuth().finally(() => setIsInitializing(false))
  }, [checkAuth])

  if (isInitializing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-aira-bg">
        <div className="w-8 h-8 border-2 border-aira-border border-t-aira-primary rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/chat" replace />} />
        <Route path="chat" element={<Chat />} />
        <Route path="chat/:chatId" element={<Chat />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="workspace" element={<Workspace />} />
        <Route path="projects" element={<Projects />} />
      </Route>
      <Route path="*" element={<Navigate to="/chat" replace />} />
    </Routes>
  )
}
