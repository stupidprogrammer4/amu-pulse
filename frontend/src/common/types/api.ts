/**
 * Mirrors the backend's `APIResponse` envelope (src/web/response.py).
 * Every endpoint answers with this shape, success or failure.
 */

export interface ApiError {
  message: string
  message_code?: string | null
  /** Field path for validation errors, e.g. ['window', 'days']. */
  loc?: (string | number)[]
  ctx?: Record<string, unknown> | null
  input?: unknown
}

export interface ApiMeta {
  page?: number
  size?: number
  total?: number
  [key: string]: unknown
}

export interface ApiResponse<T = unknown, M extends ApiMeta = ApiMeta> {
  success: boolean
  message_code?: string | null
  data?: T | null
  meta?: M | null
  /** Set when the whole request failed. */
  error?: ApiError | null
  /** Set for validation failures, or partial failures alongside `data`. */
  errors?: ApiError[] | null
}

export interface Paginated<T> {
  items: T[]
  meta: ApiMeta
}

export interface PageQuery {
  page?: number
  size?: number
}
