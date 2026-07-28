const TOKEN_STORAGE_KEY = 'amu-pulse.access_token'

export const tokenStorage = {
  get(): string | null {
    return localStorage.getItem(TOKEN_STORAGE_KEY)
  },

  set(token: string | null): void {
    if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token)
    else localStorage.removeItem(TOKEN_STORAGE_KEY)
  },

  clear(): void {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
  },
}
