import axios, { type AxiosInstance } from "axios"

const BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1"

export const api: AxiosInstance = axios.create({ baseURL: BASE })

const ACCESS_KEY = "ar_access"
const REFRESH_KEY = "ar_refresh"

export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS_KEY)
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY)
  },
  set(access: string, refresh: string) {
    localStorage.setItem(ACCESS_KEY, access)
    localStorage.setItem(REFRESH_KEY, refresh)
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

api.interceptors.request.use((config) => {
  const token = tokenStore.access
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshing: Promise<string | null> | null = null

async function tryRefresh(): Promise<string | null> {
  const refresh = tokenStore.refresh
  if (!refresh) return null
  try {
    const { data } = await axios.post(`${BASE}/auth/refresh`, { refresh_token: refresh })
    tokenStore.set(data.access_token, data.refresh_token)
    return data.access_token
  } catch {
    tokenStore.clear()
    return null
  }
}

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      refreshing = refreshing ?? tryRefresh()
      const newToken = await refreshing
      refreshing = null
      if (newToken) {
        original.headers.Authorization = `Bearer ${newToken}`
        return api(original)
      }
      if (location.pathname !== "/login") location.href = "/login"
    }
    return Promise.reject(error)
  },
)

export function apiError(e: unknown): string {
  if (axios.isAxiosError(e)) {
    const d = e.response?.data?.detail
    if (typeof d === "string") return d
    if (Array.isArray(d)) return d.map((x: any) => x.msg).join(", ")
    return e.message
  }
  return String(e)
}
