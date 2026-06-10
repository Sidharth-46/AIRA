import { create } from 'zustand'
import { authService } from '../services'

export const useAuthStore = create((set, get) => ({
  user: null,
  isAuthenticated: false,
  loading: false,
  error: null,

  signup: async (data) => {
    set({ loading: true, error: null })
    try {
      const res = await authService.signup(data)
      const { user, access_token, refresh_token } = res.data
      localStorage.setItem('aira_token', access_token)
      localStorage.setItem('aira_refresh_token', refresh_token)
      set({ user, isAuthenticated: true, loading: false })
      return true
    } catch (err) {
      set({ error: err.response?.data?.error || 'Signup failed', loading: false })
      return false
    }
  },

  login: async (data) => {
    set({ loading: true, error: null })
    try {
      const res = await authService.login(data)
      const { user, access_token, refresh_token } = res.data
      localStorage.setItem('aira_token', access_token)
      localStorage.setItem('aira_refresh_token', refresh_token)
      set({ user, isAuthenticated: true, loading: false })
      return true
    } catch (err) {
      set({ error: err.response?.data?.error || 'Login failed', loading: false })
      return false
    }
  },

  logout: async () => {
    try {
      await authService.logout()
    } catch { /* ignore */ }
    localStorage.removeItem('aira_token')
    localStorage.removeItem('aira_refresh_token')
    localStorage.removeItem('aira_chat_drafts')
    set({ user: null, isAuthenticated: false })
  },

  checkAuth: async () => {
    const token = localStorage.getItem('aira_token')
    if (!token) {
      set({ isAuthenticated: false })
      return false
    }
    try {
      const res = await authService.getProfile()
      set({ user: res.data.user, isAuthenticated: true })
      return true
    } catch {
      localStorage.removeItem('aira_token')
      localStorage.removeItem('aira_refresh_token')
      set({ user: null, isAuthenticated: false })
      return false
    }
  },

  clearError: () => set({ error: null }),
}))
