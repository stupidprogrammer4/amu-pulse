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

/**
 * What the backend actually sends back (`PagerMeta` in the contract): totals and
 * the two edge flags. It does *not* echo `page`/`per_page` — the caller sent
 * those, so the caller is the one that remembers them.
 */
export interface PagerMeta {
  total_items: number
  total_pages: number
  has_prev: boolean
  has_next: boolean
}

/** A filter the backend offers for a list route, described rather than hardcoded. */
export interface FilterMeta {
  id?: number | null
  type: 'slider' | 'checkbox' | 'radio'
  title?: string | null
  options: Record<string, unknown>[]
}

export interface BaseMeta {
  pager?: PagerMeta | null
  filters?: Record<string, FilterMeta> | null
}

/** A payload plus whatever metadata came with it, for paged reads. */
export interface Paged<TData, TMeta = BaseMeta> {
  data: TData[]
  meta: TMeta | null
}
