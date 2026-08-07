/**
 * The backend answers every route with the same envelope (see
 * `src/web/response.py`): a success flag, the payload under `data`, paging or
 * search metadata under `meta`, and errors under `error`/`errors`.
 */
export interface ApiFieldError {
  message?: string
  message_code?: string
  loc?: (string | number)[]
  ctx?: Record<string, unknown> | null
  input?: unknown
}

export interface ApiEnvelope<TData = unknown, TMeta = unknown> {
  success: boolean
  message_code?: string | null
  data?: TData | null
  meta?: TMeta | null
  error?: ApiFieldError | null
  errors?: ApiFieldError[] | null
}

export interface PagerMeta {
  page: number
  per_page: number
  total_items: number
  total_pages: number
}

export interface BaseMeta {
  pager?: PagerMeta | null
}

/** A payload plus whatever metadata came with it, for paged reads. */
export interface Paged<TData, TMeta = BaseMeta> {
  data: TData[]
  meta: TMeta | null
}
