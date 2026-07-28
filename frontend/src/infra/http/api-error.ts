import type { ApiError } from '@/common/types/api'

/**
 * Every failure the app sees — transport, HTTP status, or a `success: false`
 * envelope — arrives as one of these, so callers never branch on axios internals.
 */
export class ApiRequestError extends Error {
  readonly status: number | null
  readonly messageCode: string | null
  readonly errors: ApiError[]

  constructor(
    message: string,
    options: { status?: number | null; messageCode?: string | null; errors?: ApiError[] } = {},
  ) {
    super(message)
    this.name = 'ApiRequestError'
    this.status = options.status ?? null
    this.messageCode = options.messageCode ?? null
    this.errors = options.errors ?? []
  }

  get isUnauthorized(): boolean {
    return this.status === 401
  }

  get isValidation(): boolean {
    return this.status === 422 || this.errors.length > 0
  }

  /** Validation errors keyed by field path, for binding to form inputs. */
  get fieldErrors(): Record<string, string> {
    const result: Record<string, string> = {}
    for (const error of this.errors) {
      const key = error.loc?.join('.') ?? '_'
      if (!(key in result)) result[key] = error.message
    }
    return result
  }
}
