/**
 * Every environment-driven value the panel reads, resolved once and frozen.
 * Views import from here rather than touching `import.meta.env`, so a renamed
 * variable is a single edit and a missing one has an obvious default.
 */
export const env = Object.freeze({
  apiBaseUrl: (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, ''),
  appTitle: import.meta.env.VITE_APP_TITLE || 'AMU Pulse System Panel',
  environment: import.meta.env.VITE_ENVIRONMENT || 'development',
  requestTimeout: Number(import.meta.env.VITE_REQUEST_TIMEOUT ?? 20000),
})

export function apiUrl(path: string): string {
  return `${env.apiBaseUrl}/${path.replace(/^\//, '')}`
}
