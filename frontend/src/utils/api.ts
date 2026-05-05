import axios, { type AxiosResponse } from 'axios'
import { API_BASE } from './constants'
import type { ApiError } from '@/types/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error),
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.data?.error) {
      const apiErr: ApiError = error.response.data
      return Promise.reject(new Error(apiErr.error.message || '请求失败'))
    }
    const message = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(message))
  },
)

export async function typedGet<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const res: AxiosResponse<T> = await api.get(url, { params })
  return res.data
}

export async function typedPost<T>(url: string, data?: unknown): Promise<T> {
  const res: AxiosResponse<T> = await api.post(url, data)
  return res.data
}

export async function typedPut<T>(url: string, data?: unknown): Promise<T> {
  const res: AxiosResponse<T> = await api.put(url, data)
  return res.data
}

export async function typedDelete<T>(url: string): Promise<T> {
  const res: AxiosResponse<T> = await api.delete(url)
  return res.data
}

export default api
