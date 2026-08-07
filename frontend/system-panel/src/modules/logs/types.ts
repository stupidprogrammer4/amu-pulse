import type { BaseMeta } from '@/infra/http'

export const logLevels = ['debug', 'info', 'warning', 'error', 'critical'] as const
export type LogLevel = (typeof logLevels)[number]

export const logBuckets = ['5m', '1h', '5h', '1d'] as const
export type LogBucket = (typeof logBuckets)[number]

export interface NamedOut {
  name?: string | null
}

export interface OriginFileOut {
  name?: string | null
  path?: string | null
  line?: number | null
}

export interface OriginOut {
  function?: string | null
  file?: OriginFileOut | null
}

export interface LogDetailOut {
  level?: string | null
  logger?: string | null
  origin?: OriginOut | null
}

export interface LogErrorOut {
  type?: string | null
  message?: string | null
  stack_trace?: string | null
}

export interface LogOut {
  timestamp: string
  message?: string | null
  request_id?: string | null
  stream?: string | null
  log?: LogDetailOut | null
  error?: LogErrorOut | null
  service?: NamedOut | null
  container?: NamedOut | null
}

/** `levels`, `loggers` and `containers` are facet counts for the current query. */
export interface LogMeta extends BaseMeta {
  levels: Record<string, number>
  loggers: Record<string, number>
  containers: Record<string, number>
}

export interface LogPointOut {
  count: number
  timestamp: string
}

export interface LogChartOut {
  bucket: LogBucket
  points: LogPointOut[]
  min: number
  max: number
  mean: number
}

/** The chart route advertises what it can be asked for, rather than us guessing. */
export interface LogChartMeta extends BaseMeta {
  levels: string[]
  containers: string[]
  buckets: LogBucket[]
}

export interface LogSearchQuery {
  q?: string
  levels?: LogLevel[]
  loggers?: string[]
  containers?: string[]
  request_id?: string
  from_time?: string
  to_time?: string
  page?: number
  per_page?: number
}

export interface LogChartQuery {
  bucket: LogBucket
  container: string
  level?: LogLevel
}
