import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'Unknown error'
    return Promise.reject(new Error(msg))
  }
)

export const WS_BASE = BASE_URL.replace(/^http/, 'ws')
