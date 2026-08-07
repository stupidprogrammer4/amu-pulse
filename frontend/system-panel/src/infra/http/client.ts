import axios, {
  AxiosError,
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'

import { apiUrl, env } from '@/core/config/env'

import { ApiError } from './api-error'
import type { ApiEnvelope, Paged } from './envelope'
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from './token-storage'

/** Flags a request that already came back from a refresh-and-retry. */
interface RetryableConfig extends InternalAxiosRequestConfig {
  _retried?: boolean
  /** Skips the Authorization header — only login and refresh set this. */
  _anonymous?: boolean
}

export const http: AxiosInstance = axios.create({
  baseURL: env.apiBaseUrl,
  timeout: env.requestTimeout,
  headers: { Accept: 'application/json' },
})

/**
 * The router installs this so a dead session lands on the login page instead of
 * leaving the operator staring at an empty table.
 */
let onSessionLost: (() => void) | null = null

export function setSessionLostHandler(handler: () => void): void {
  onSessionLost = handler
}

http.interceptors.request.use((config: RetryableConfig) => {
  const token = getAccessToken()
  if (token && !config._anonymous) config.headers.set('Authorization', `Bearer ${token}`)
  return config
})

/**
 * One refresh in flight at a time. Without this a dashboard that fires six
 * parallel reads on mount would fire six refreshes, and five of them would
 * rotate a token the sixth was about to use.
 */
let refreshInFlight: Promise<boolean> | null = null

async function refreshSession(): Promise<boolean> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return false
  try {
    const response = await axios.post<ApiEnvelope<{ access_token: string; refresh_token: string }>>(
      apiUrl('/auth/admins/refresh'),
      { refresh_token: refreshToken },
      { timeout: env.requestTimeout, headers: { Accept: 'application/json' } },
    )
    const data = response.data?.data
    if (!response.data?.success || !data?.access_token) return false
    setTokens(data.access_token, data.refresh_token ?? refreshToken)
    return true
  } catch {
    return false
  }
}

function ensureRefresh(): Promise<boolean> {
  refreshInFlight ??= refreshSession().finally(() => {
    refreshInFlight = null
  })
  return refreshInFlight
}

http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiEnvelope>) => {
    const config = error.config as RetryableConfig | undefined
    const status = error.response?.status ?? 0

    if (status === 401 && config && !config._retried && !config._anonymous) {
      config._retried = true
      if (await ensureRefresh()) return http.request(config)
      clearTokens()
      onSessionLost?.()
    }

    if (status === 401 && !config?._anonymous) {
      clearTokens()
      onSessionLost?.()
    }

    throw ApiError.fromEnvelope(error.response?.data, status)
  },
)

/** Unwraps the envelope and hands back just the payload. */
export async function request<TData>(config: AxiosRequestConfig): Promise<TData> {
  const response: AxiosResponse<ApiEnvelope<TData>> = await http.request(config)
  if (!response.data?.success) throw ApiError.fromEnvelope(response.data, response.status)
  return response.data.data as TData
}

/** Same call, but keeps `meta` — the paging every search route returns. */
export async function requestPaged<TData, TMeta = unknown>(
  config: AxiosRequestConfig,
): Promise<Paged<TData, TMeta>> {
  const response: AxiosResponse<ApiEnvelope<TData, TMeta>> = await http.request(config)
  if (!response.data?.success) throw ApiError.fromEnvelope(response.data, response.status)
  const data = response.data.data
  return {
    data: (Array.isArray(data) ? data : data ? [data] : []) as TData[],
    meta: (response.data.meta ?? null) as TMeta | null,
  }
}

/** Sends a request without an Authorization header — login and refresh only. */
export function anonymousRequest<TData>(config: AxiosRequestConfig): Promise<TData> {
  return request<TData>({ ...config, _anonymous: true } as AxiosRequestConfig)
}

/* ------------------------------------------------------------------ *
 * Raw transport — the API explorer's channel.
 *
 * The explorer must show what the backend actually answered: a 422 body, an
 * error envelope, a redirect. So it gets its own instance that never rejects
 * and never unwraps, while still carrying the session token.
 * ------------------------------------------------------------------ */

export interface RawRequestInput {
  method: string
  /** Path relative to the API base, e.g. `/panel/logs`. */
  path: string
  query?: Record<string, string | string[]>
  headers?: Record<string, string>
  /** Sent as-is; already-parsed JSON, a string, or undefined for no body. */
  body?: unknown
}

export interface RawResponse {
  status: number
  statusText: string
  durationMs: number
  contentType: string
  headers: Record<string, string>
  /** Decoded text, or a placeholder line when the payload is binary. */
  body: string
  bytes: number
  url: string
}

const rawHttp = axios.create({
  baseURL: env.apiBaseUrl,
  timeout: env.requestTimeout,
  responseType: 'blob',
  // Every status is a result worth showing, not a throw.
  validateStatus: () => true,
})

rawHttp.interceptors.request.use((config: RetryableConfig) => {
  const token = getAccessToken()
  if (token) config.headers.set('Authorization', `Bearer ${token}`)
  return config
})

function isTextual(contentType: string): boolean {
  return (
    contentType.includes('json') ||
    contentType.startsWith('text/') ||
    contentType.includes('xml') ||
    contentType.includes('javascript')
  )
}

export async function rawRequest(input: RawRequestInput): Promise<RawResponse> {
  const config: AxiosRequestConfig = {
    method: input.method.toLowerCase(),
    url: `/${input.path.replace(/^\//, '')}`,
    params: input.query,
    headers: input.headers,
    data: input.body,
  }

  const started = performance.now()
  let response = await rawHttp.request<Blob>(config)
  // An expired access token would otherwise read as a real 401 from the route
  // under test, so rotate once and repeat before reporting.
  if (response.status === 401 && (await ensureRefresh())) {
    response = await rawHttp.request<Blob>(config)
  }
  const durationMs = Math.round(performance.now() - started)

  const blob = response.data
  const contentType = String(response.headers['content-type'] ?? blob?.type ?? '')
  const bytes = blob?.size ?? 0
  const body = blob
    ? isTextual(contentType)
      ? await blob.text()
      : `[binary payload · ${bytes.toLocaleString('en-US')} bytes]`
    : ''

  return {
    status: response.status,
    statusText: response.statusText,
    durationMs,
    contentType,
    headers: Object.fromEntries(
      Object.entries(response.headers).map(([key, value]) => [key, String(value)]),
    ),
    body,
    bytes,
    url: displayUrl(String(config.url), input.query),
  }
}

/** What the operator should see they just called, query string included. */
function displayUrl(path: string, query?: RawRequestInput['query']): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(query ?? {})) {
    for (const entry of Array.isArray(value) ? value : [value]) search.append(key, entry)
  }
  const suffix = search.toString()
  return `${env.apiBaseUrl}${path}${suffix ? `?${suffix}` : ''}`
}
