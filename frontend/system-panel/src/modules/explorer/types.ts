export type HttpMethod = 'get' | 'post' | 'put' | 'patch' | 'delete' | 'head' | 'options'

export const HTTP_METHODS: HttpMethod[] = [
  'get',
  'post',
  'put',
  'patch',
  'delete',
  'head',
  'options',
]

export interface OpenApiSchema {
  $ref?: string
  type?: string
  format?: string
  title?: string
  description?: string
  default?: unknown
  example?: unknown
  examples?: unknown[]
  enum?: unknown[]
  required?: string[]
  properties?: Record<string, OpenApiSchema>
  items?: OpenApiSchema
  anyOf?: OpenApiSchema[]
  oneOf?: OpenApiSchema[]
  allOf?: OpenApiSchema[]
  nullable?: boolean
  additionalProperties?: boolean | OpenApiSchema
  minimum?: number
  maximum?: number
}

export interface OpenApiParameter {
  name: string
  in: 'path' | 'query' | 'header' | 'cookie'
  required?: boolean
  description?: string
  deprecated?: boolean
  schema?: OpenApiSchema
  example?: unknown
}

export interface OpenApiMediaType {
  schema?: OpenApiSchema
  example?: unknown
}

export interface OpenApiRequestBody {
  required?: boolean
  description?: string
  content?: Record<string, OpenApiMediaType>
}

export interface RawOperation {
  tags?: string[]
  summary?: string
  description?: string
  operationId?: string
  deprecated?: boolean
  parameters?: OpenApiParameter[]
  requestBody?: OpenApiRequestBody
  responses?: Record<string, { description?: string; content?: Record<string, OpenApiMediaType> }>
}

export type PathItem = Partial<Record<HttpMethod, RawOperation>> & {
  parameters?: OpenApiParameter[]
  summary?: string
}

export interface OpenApiDocument {
  openapi: string
  info: { title: string; version: string; description?: string }
  paths: Record<string, PathItem>
  components?: { schemas?: Record<string, OpenApiSchema> }
}

/**
 * The backend's guards read the Authorization header by hand rather than
 * declaring a FastAPI security scheme, so the contract carries no `security`
 * block. The level is inferred from the path instead — see `guardFor`.
 */
export type GuardLevel = 'public' | 'admin' | 'super-admin'

export interface Operation {
  /** Stable key: `get:/panel/logs`. */
  id: string
  method: HttpMethod
  path: string
  tag: string
  summary: string
  description?: string
  deprecated: boolean
  parameters: OpenApiParameter[]
  requestBody?: OpenApiRequestBody
  guard: GuardLevel
  /** True for the guarded `/panel/*` surface this console exists to drive. */
  isPanel: boolean
}
