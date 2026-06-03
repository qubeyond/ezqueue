import type { TokenResponse } from '@/types/api'

let accessToken = ''

export const ROOM_KEY = 'q_room_id'
export const ROLE_KEY = 'q_role'

export function getAccessToken(): string {
  return accessToken
}

export function setAccessToken(token: string): void {
  accessToken = token
}

export function clearAccessToken(): void {
  accessToken = ''
}

export function authHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${accessToken}`,
  }
}

export async function ensureToken(): Promise<void> {
  if (accessToken) return

  const refreshRes = await fetch('/api/v1/auth/refresh', {
    method: 'POST',
    credentials: 'include',
  })
  if (refreshRes.ok) {
    const data: TokenResponse = await refreshRes.json()
    accessToken = data.access_token
    return
  }

  // Личность выдаёт сервер (в httpOnly refresh-куке). Клиент ничего не задаёт.
  const res = await fetch('/api/v1/auth/token', {
    method: 'POST',
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Ошибка получения токена')
  const data: TokenResponse = await res.json()
  accessToken = data.access_token
}

export async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
  await ensureToken()
  options.credentials = 'include'
  options.headers = { ...authHeaders(), ...(options.headers as Record<string, string> || {}) }

  const res = await fetch(url, options)
  if (res.status === 401) {
    const refreshRes = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    })
    if (refreshRes.ok) {
      const data: TokenResponse = await refreshRes.json()
      accessToken = data.access_token
      options.headers = { ...authHeaders(), ...(options.headers as Record<string, string> || {}) }
      return fetch(url, options)
    }
    accessToken = ''
    throw new Error('Сессия истекла. Попробуйте снова.')
  }
  return res
}
