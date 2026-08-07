/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_APP_TITLE?: string
  readonly VITE_ENVIRONMENT?: string
  readonly VITE_REQUEST_TIMEOUT?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
