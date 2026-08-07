import type { ApiEnvelope, ApiFieldError } from './envelope'

/**
 * One error type for the whole panel. Whatever the failure was — a 422 from
 * pydantic, a domain error, a dead network — a caller only ever catches this
 * and reads `.message`.
 */
export class ApiError extends Error {
  readonly status: number
  readonly messageCode?: string
  readonly fieldErrors: ApiFieldError[]

  constructor(
    message: string,
    status: number,
    messageCode?: string,
    fieldErrors: ApiFieldError[] = [],
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.messageCode = messageCode
    this.fieldErrors = fieldErrors
  }

  /** True when the caller can fix this by editing the form they just sent. */
  get isValidation(): boolean {
    return this.status === 422 || this.fieldErrors.length > 0
  }

  static fromEnvelope(envelope: ApiEnvelope | null | undefined, status: number): ApiError {
    const errors = envelope?.errors ?? []
    const message = envelope?.error?.message ?? errors[0]?.message ?? defaultMessage(status)
    return new ApiError(
      message,
      status,
      envelope?.error?.message_code ??
        errors[0]?.message_code ??
        envelope?.message_code ??
        undefined,
      errors,
    )
  }
}

function defaultMessage(status: number): string {
  if (status === 0) return 'The backend could not be reached.'
  if (status === 401) return 'Your session has expired. Sign in again.'
  if (status === 403) return 'This account is not allowed to perform that action.'
  if (status === 404) return 'The requested resource does not exist.'
  if (status >= 500) return 'The backend failed while handling the request.'
  return `Request failed with status ${status}.`
}
