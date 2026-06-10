import { create } from 'zustand'
import { dashboardService } from '../services'

export const useDashboardStore = create((set) => ({
  stats: null,
  activity: [],
  usage: [],
  loading: false,

  fetchDashboardData: async () => {
    set({ loading: true })
    try {
      const [statsRes, activityRes, usageRes] = await Promise.all([
        dashboardService.getStats(),
        dashboardService.getActivity(),
        dashboardService.getUsage()
      ])
      
      set({
        stats: statsRes.data.stats,
        activity: activityRes.data.activity,
        usage: usageRes.data.usage,
        loading: false
      })
    } catch (err) {
      console.error('Failed to fetch dashboard data', err)
      set({ loading: false })
    }
  }
}))
