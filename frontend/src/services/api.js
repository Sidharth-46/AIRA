import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor — attach JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('aira_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor — handle 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      try {
        const refreshToken = localStorage.getItem('aira_refresh_token')
        if (refreshToken) {
          const { data } = await axios.post(`${API_URL}/api/auth/refresh`, {}, {
            headers: { Authorization: `Bearer ${refreshToken}` },
          })
          localStorage.setItem('aira_token', data.access_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        }
      } catch {
        localStorage.removeItem('aira_token')
        localStorage.removeItem('aira_refresh_token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
