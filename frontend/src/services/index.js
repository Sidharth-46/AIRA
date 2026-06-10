import api from './api'

export const authService = {
  signup: (data) => api.post('/api/auth/signup', data),
  login: (data) => api.post('/api/auth/login', data),
  refresh: () => api.post('/api/auth/refresh'),
  getProfile: () => api.get('/api/auth/me'),
  logout: () => api.post('/api/auth/logout'),
}

export const chatService = {
  getChats: (params) => api.get('/api/chats', { params }),
  createChat: (data) => api.post('/api/chats', data),
  getChat: (id) => api.get(`/api/chats/${id}`),
  updateChat: (id, data) => api.put(`/api/chats/${id}`, data),
  deleteChat: (id) => api.delete(`/api/chats/${id}`),
  getFolders: () => api.get('/api/chats/folders'),

  // SSE streaming for messages
  sendMessage: (chatId, content, workspaceContext = null) => {
    const token = localStorage.getItem('aira_token')
    
    const body = { content }
    if (workspaceContext && workspaceContext.projectId) {
      body.workspace_context = workspaceContext
    }

    return fetch(`/api/chats/${chatId}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    })
  },
}

export const projectService = {
  getProjects: (params) => api.get('/api/projects', { params }),
  getProject: (id) => api.get(`/api/projects/${id}`),
  uploadProject: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/api/projects/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  deleteProject: (id) => api.delete(`/api/projects/${id}`),
  analyzeProject: (id) => api.post(`/api/projects/${id}/analyze`),
}

export const workspaceService = {
  getTree: (project) => api.get('/api/workspace/tree', { params: { project } }),
  readFile: (path, project) => api.get('/api/workspace/file', { params: { path, project } }),
  saveFile: (path, content, project) => api.put('/api/workspace/file', { path, content, project }),
  createFile: (data) => api.post('/api/workspace/file', data), // Assuming data already includes project if needed
  deleteFile: (path, project) => api.delete('/api/workspace/file', { params: { path, project } }),
  search: (q, project) => api.get('/api/workspace/search', { params: { q, project } }),
}

export const dashboardService = {
  getStats: () => api.get('/api/dashboard/stats'),
  getActivity: () => api.get('/api/dashboard/activity'),
  getUsage: () => api.get('/api/dashboard/usage'),
}

export const modelService = {
  getModels: () => api.get('/api/models'),
  getActive: () => api.get('/api/models/active'),
  switchModel: (model) => api.put('/api/models/active', { model }),
  getStatus: () => api.get('/api/models/status'),
}
