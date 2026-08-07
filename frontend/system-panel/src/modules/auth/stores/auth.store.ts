import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { ApiError, clearTokens, hasSession, setTokens } from '@/infra/http'

import { authService } from '../services/auth.service'
import type { Admin, LoginPayload } from '../types'

const ADMIN_KEY = 'amu.system-panel.admin'

function readCachedAdmin(): Admin | null {
  try {
    const raw = localStorage.getItem(ADMIN_KEY)
    return raw ? (JSON.parse(raw) as Admin) : null
  } catch {
    return null
  }
}

function cacheAdmin(admin: Admin | null): void {
  try {
    if (admin) localStorage.setItem(ADMIN_KEY, JSON.stringify(admin))
    else localStorage.removeItem(ADMIN_KEY)
  } catch {
    /* storage is optional; the identity is re-fetched from /auth/admins/me anyway */
  }
}

export const useAuthStore = defineStore('auth', () => {
  // Cached so a reload paints the sidebar identity before /me answers.
  const admin = ref<Admin | null>(readCachedAdmin())
  const pending = ref(false)
  const error = ref<string | null>(null)
  const resolved = ref(false)

  const isAuthenticated = computed(() => hasSession())
  const isSuperAdmin = computed(() => admin.value?.is_super_admin === true)
  const displayName = computed(() => admin.value?.username ?? 'unknown')
  const initials = computed(() => (admin.value?.username ?? '?').slice(0, 2).toUpperCase())

  function setAdmin(next: Admin | null): void {
    admin.value = next
    cacheAdmin(next)
  }

  async function login(payload: LoginPayload): Promise<void> {
    pending.value = true
    error.value = null
    try {
      const auth = await authService.login(payload)
      setTokens(auth.access_token, auth.refresh_token)
      setAdmin(auth.admin)
      resolved.value = true
    } catch (cause) {
      error.value = cause instanceof ApiError ? cause.message : 'Sign in failed.'
      throw cause
    } finally {
      pending.value = false
    }
  }

  /**
   * Confirms the stored token still belongs to a live admin. Called once by the
   * router guard, so a revoked account cannot linger on a cached identity.
   */
  async function restore(): Promise<boolean> {
    if (resolved.value) return isAuthenticated.value
    if (!hasSession()) {
      resolved.value = true
      return false
    }
    try {
      setAdmin(await authService.me())
      return true
    } catch {
      clearTokens()
      setAdmin(null)
      return false
    } finally {
      resolved.value = true
    }
  }

  function logout(): void {
    clearTokens()
    setAdmin(null)
    resolved.value = true
    error.value = null
  }

  return {
    admin,
    pending,
    error,
    isAuthenticated,
    isSuperAdmin,
    displayName,
    initials,
    login,
    logout,
    restore,
  }
})
