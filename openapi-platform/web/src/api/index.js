import axios from 'axios'

const api = axios.create({
  baseURL: '/api'
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const auth = {
  login: (username, password) => api.post('/auth/login', new URLSearchParams({ username, password })),
  register: (data) => api.post('/auth/register', data),
  refresh: (refresh_token) => api.post('/auth/refresh', null, { params: { refresh_token } })
}

export const apiKeys = {
  list: () => api.get('/api-keys'),
  create: (data) => api.post('/api-keys', data),
  delete: (id) => api.delete(`/api-keys/${id}`),
  toggle: (id) => api.post(`/api-keys/${id}/toggle`)
}

export const oauthApps = {
  list: () => api.get('/oauth/apps'),
  create: (data) => api.post('/oauth/apps', data),
  delete: (id) => api.delete(`/oauth/apps/${id}`)
}

export const managedApis = {
  list: () => api.get('/managed-apis'),
  create: (data) => api.post('/managed-apis', data),
  update: (id, data) => api.put(`/managed-apis/${id}`, data),
  delete: (id) => api.delete(`/managed-apis/${id}`)
}

export default api
