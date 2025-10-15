import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: (import.meta as any).env?.VITE_API_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token等
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // 统一错误处理
    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 401:
          // 未授权，清除token并跳转到登录页
          localStorage.removeItem('token')
          window.location.href = '/login'
          break
        case 403:
          console.error('权限不足')
          break
        case 404:
          console.error('请求的资源不存在')
          break
        case 500:
          console.error('服务器内部错误')
          break
        default:
          console.error(`请求失败: ${status}`)
      }

      // 返回错误信息
      return Promise.reject({
        message: data?.message || `请求失败: ${status}`,
        status,
        data
      })
    } else if (error.request) {
      // 网络错误
      console.error('网络错误，请检查网络连接')
      return Promise.reject({
        message: '网络错误，请检查网络连接',
        status: 0
      })
    } else {
      // 其他错误
      console.error('请求配置错误')
      return Promise.reject({
        message: '请求配置错误',
        status: -1
      })
    }
  }
)

export { api }
