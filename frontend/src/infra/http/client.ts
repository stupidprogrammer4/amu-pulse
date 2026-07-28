import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'

import type { ApiMeta, ApiResponse } from '@/common/types/api'
import { env } from '@/core/config/env'
import { ApiRequestError } from './api-error'
import { tokenStorage } from './token-storage'

export const http: AxiosInstance = axios.create({
  baseURL: env.apiBaseUrl,
  timeout: env.requestTimeout,
  headers: { Accept: 'application/json' },
})

http.interceptors.request.use((config) => {
  const token = tokenStorage.get()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

/** Called on any 401 so the app can drop the session and redirect. */
let onUnauthorized: (() => void) | null = null

export function setUnauthorizedHandler(handler: () => void): void {
  onUnauthorized = handler
}

function toApiError(error: unknown): ApiRequestError {
  if (!axios.isAxiosError(error)) {
    return new ApiRequestError(error instanceof Error ? error.message : 'خطای غیرمنتظره')
  }

  if (!error.response) {
    const timedOut = error.code === 'ECONNABORTED'
    return new ApiRequestError(
      timedOut ? 'زمان درخواست به پایان رسید' : 'ارتباط با سرور برقرار نشد',
      {
        messageCode: timedOut ? 'timeout' : 'network_error',
      },
    )
  }

  const { status, data } = error.response
  const envelope = data as ApiResponse | undefined
  const errors = envelope?.errors ?? []
  const message = envelope?.error?.message ?? errors[0]?.message ?? 'درخواست ناموفق بود'

  return new ApiRequestError(message, {
    status,
    messageCode: envelope?.error?.message_code ?? envelope?.message_code ?? null,
    errors: envelope?.error ? [envelope.error, ...errors] : errors,
  })
}

http.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    const apiError = toApiError(error)
    if (apiError.isUnauthorized) {
      tokenStorage.clear()
      onUnauthorized?.()
    }
    return Promise.reject(apiError)
  },
)

/**
 * Unwraps the backend envelope: returns `data`, or throws `ApiRequestError`
 * when the backend answered 2xx with `success: false`.
 */
function unwrap<T>(response: ApiResponse<T>): T {
  if (!response.success) {
    const errors = response.errors ?? []
    throw new ApiRequestError(
      response.error?.message ?? errors[0]?.message ?? 'درخواست ناموفق بود',
      {
        messageCode: response.error?.message_code ?? response.message_code ?? null,
        errors: response.error ? [response.error, ...errors] : errors,
      },
    )
  }
  return response.data as T
}

export async function request<T>(config: AxiosRequestConfig): Promise<T> {
  const response = await http.request<ApiResponse<T>>(config)
  return unwrap(response.data)
}

/** Same as `request`, but keeps `meta` — use it for paginated endpoints. */
export async function requestWithMeta<T, M extends ApiMeta = ApiMeta>(
  config: AxiosRequestConfig,
): Promise<{ data: T; meta: M | null }> {
  const response = await http.request<ApiResponse<T, M>>(config)
  return { data: unwrap(response.data), meta: response.data.meta ?? null }
}

export const api = {
  get: <T>(url: string, params?: unknown, config?: AxiosRequestConfig) =>
    request<T>({ ...config, method: 'GET', url, params }),
  post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    request<T>({ ...config, method: 'POST', url, data }),
  patch: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    request<T>({ ...config, method: 'PATCH', url, data }),
  put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    request<T>({ ...config, method: 'PUT', url, data }),
  delete: <T>(url: string, config?: AxiosRequestConfig) =>
    request<T>({ ...config, method: 'DELETE', url }),
}
