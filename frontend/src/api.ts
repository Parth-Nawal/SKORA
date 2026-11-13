const BASE = import.meta.env.VITE_API_URL || ''
export function getToken() { return localStorage.getItem('skora_token') || '' }
export async function api<T = any>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {})
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  const response = await fetch(`${BASE}/api${path}`, { ...options, headers })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`)
  return data as T
}
export function saveSession(data: any) {
  localStorage.setItem('skora_token', data.access_token)
  localStorage.setItem('skora_user', JSON.stringify(data.user))
}
export function clearSession() {
  localStorage.removeItem('skora_token')
  localStorage.removeItem('skora_user')
}
