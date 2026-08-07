import { reactive, readonly } from 'vue'

/**
 * The tokens live here rather than in the Pinia store so the axios interceptor
 * can read and rotate them without importing a store — which would close a
 * cycle, since the store is built on top of the client.
 */
const ACCESS_KEY = 'amu.system-panel.access'
const REFRESH_KEY = 'amu.system-panel.refresh'

const state = reactive({
  accessToken: read(ACCESS_KEY),
  refreshToken: read(REFRESH_KEY),
})

function read(key: string): string {
  try {
    return localStorage.getItem(key) ?? ''
  } catch {
    return ''
  }
}

function write(key: string, value: string): void {
  try {
    if (value) localStorage.setItem(key, value)
    else localStorage.removeItem(key)
  } catch {
    /* private mode or a blocked storage quota — the session just stays in memory */
  }
}

export const tokens = readonly(state)

export function hasSession(): boolean {
  return Boolean(state.accessToken)
}

export function getAccessToken(): string {
  return state.accessToken
}

export function getRefreshToken(): string {
  return state.refreshToken
}

export function setTokens(accessToken: string, refreshToken: string): void {
  state.accessToken = accessToken
  state.refreshToken = refreshToken
  write(ACCESS_KEY, accessToken)
  write(REFRESH_KEY, refreshToken)
}

export function clearTokens(): void {
  state.accessToken = ''
  state.refreshToken = ''
  write(ACCESS_KEY, '')
  write(REFRESH_KEY, '')
}
