import axios from 'axios'

const apiClient = axios.create({
  baseURL: '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加 Token
apiClient.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
apiClient.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
      return Promise.reject(data.detail || '请求失败')
    }
    return Promise.reject(error.message || '网络错误')
  }
)

// ===== 用户认证 =====
export const authApi = {
  register: (data) => apiClient.post('/api/auth/register', data),
  login: (username, password) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    return apiClient.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  getProfile: () => apiClient.get('/api/user/profile'),
  updateProfile: (data) => apiClient.put('/api/user/profile', data)
}

// ===== 应用管理 =====
export const appApi = {
  list: (page = 1, pageSize = 10) => 
    apiClient.get(`/api/apps?page=${page}&page_size=${pageSize}`),
  get: (id) => apiClient.get(`/api/apps/${id}`),
  create: (data) => apiClient.post('/api/apps', data),
  update: (id, data) => apiClient.put(`/api/apps/${id}`, data),
  delete: (id) => apiClient.delete(`/api/apps/${id}`),
  resetSecret: (id) => apiClient.post(`/api/apps/${id}/reset-secret`)
}

// ===== 接口管理 =====
export const apiApi = {
  list: (page = 1, pageSize = 10, status = '', keyword = '', appId = '') => {
    let url = `/api/openapis?page=${page}&page_size=${pageSize}`
    if (status) url += `&status=${status}`
    if (keyword) url += `&keyword=${keyword}`
    if (appId) url += `&app_id=${appId}`
    return apiClient.get(url)
  },
  get: (id) => apiClient.get(`/api/openapis/${id}`),
  create: (data) => apiClient.post('/api/openapis', data),
  update: (id, data) => apiClient.put(`/api/openapis/${id}`, data),
  delete: (id) => apiClient.delete(`/api/openapis/${id}`),
  publish: (id) => apiClient.post(`/api/openapis/${id}/publish`),
  unpublish: (id) => apiClient.post(`/api/openapis/${id}/unpublish`),
  
  // 权限管理
  grantAccess: (apiId, appId) => 
    apiClient.post(`/api/openapis/${apiId}/access`, { app_id: appId }),
  listAccess: (apiId) => apiClient.get(`/api/openapis/${apiId}/access`),
  revokeAccess: (apiId, appId) => 
    apiClient.delete(`/api/openapis/${apiId}/access/${appId}`),
  
  // 接口测试
  test: (apiId, data) => apiClient.post(`/api/openapis/${apiId}/test`, data)
}

// ===== 通用 =====
export default apiClient
