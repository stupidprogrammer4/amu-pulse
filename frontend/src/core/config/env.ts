/** Single place that reads import.meta.env, so nothing else has to. */
export const env = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
  appTitle: import.meta.env.VITE_APP_TITLE || 'نبض طلا',
  requestTimeout: Number(import.meta.env.VITE_REQUEST_TIMEOUT ?? 15000),
  isDev: import.meta.env.DEV,
} as const
