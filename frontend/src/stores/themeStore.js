import { create } from 'zustand'

export const useThemeStore = create((set) => ({
  theme: localStorage.getItem('aira_theme') || 'dark',

  toggleTheme: () => {
    set((s) => {
      const next = s.theme === 'dark' ? 'light' : 'dark'
      localStorage.setItem('aira_theme', next)
      document.documentElement.classList.toggle('light', next === 'light')
      console.log('THEME_CHANGED', next)
      return { theme: next }
    })
  },

  initTheme: () => {
    const saved = localStorage.getItem('aira_theme') || 'dark'
    document.documentElement.classList.toggle('light', saved === 'light')
    set({ theme: saved })
  },
}))
