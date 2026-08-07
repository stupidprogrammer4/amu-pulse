import type { OpenApiDocument, OpenApiSchema } from '../types'

const REF_PREFIX = '#/components/schemas/'

/**
 * Follows a `$ref` to the schema it names. Self-referencing models (a tree
 * node, a nested config) would otherwise loop, so the chain is bounded.
 */
export function resolveSchema(
  document: OpenApiDocument | null,
  schema: OpenApiSchema | undefined,
  depth = 0,
): OpenApiSchema | undefined {
  if (!schema?.$ref || depth > 8) return schema
  if (!schema.$ref.startsWith(REF_PREFIX)) return schema
  const target = document?.components?.schemas?.[schema.$ref.slice(REF_PREFIX.length)]
  return target ? resolveSchema(document, target, depth + 1) : schema
}

/**
 * Pydantic writes an optional field as `anyOf: [T, null]`. For a form we want
 * T, plus the knowledge that null is allowed.
 */
export function unwrapNullable(schema: OpenApiSchema | undefined): {
  schema: OpenApiSchema | undefined
  nullable: boolean
} {
  const branches = schema?.anyOf ?? schema?.oneOf
  if (!branches?.length) return { schema, nullable: schema?.nullable === true }
  const concrete = branches.filter((branch) => branch.type !== 'null')
  return {
    schema: concrete[0] ?? schema,
    nullable: schema?.nullable === true || concrete.length !== branches.length,
  }
}

/** A one-line type label for a form row: `integer`, `string[]`, `a | b`. */
export function describeSchema(
  document: OpenApiDocument | null,
  input: OpenApiSchema | undefined,
  depth = 0,
): string {
  if (!input || depth > 5) return 'any'
  const { schema, nullable } = unwrapNullable(resolveSchema(document, input))
  const resolved = resolveSchema(document, schema)
  if (!resolved) return 'any'

  const suffix = nullable ? ' | null' : ''
  if (resolved.enum?.length) {
    return resolved.enum.map((value) => String(value)).join(' | ') + suffix
  }
  if (resolved.type === 'array') {
    return `${describeSchema(document, resolved.items, depth + 1)}[]${suffix}`
  }
  if (resolved.type === 'object' || resolved.properties) {
    return `${resolved.title ?? 'object'}${suffix}`
  }
  const base = resolved.format ? `${resolved.type ?? 'string'} <${resolved.format}>` : resolved.type
  return `${base ?? 'any'}${suffix}`
}

/**
 * Builds a starting value for a body editor. It is a scaffold to edit, not a
 * valid payload — required fields get a typed placeholder so the operator can
 * see the shape without reading the schema.
 */
export function sampleFor(
  document: OpenApiDocument | null,
  input: OpenApiSchema | undefined,
  depth = 0,
): unknown {
  if (!input || depth > 4) return null
  const resolved = resolveSchema(document, unwrapNullable(resolveSchema(document, input)).schema)
  if (!resolved) return null

  if (resolved.example !== undefined) return resolved.example
  if (resolved.default !== undefined) return resolved.default
  if (resolved.enum?.length) return resolved.enum[0]

  if (resolved.properties) {
    const sample: Record<string, unknown> = {}
    for (const [name, property] of Object.entries(resolved.properties)) {
      sample[name] = sampleFor(document, property, depth + 1)
    }
    return sample
  }
  if (resolved.type === 'array') return [sampleFor(document, resolved.items, depth + 1)]

  switch (resolved.type) {
    case 'integer':
      return resolved.minimum ?? 0
    case 'number':
      return resolved.minimum ?? 0
    case 'boolean':
      return false
    case 'object':
      return {}
    case 'null':
      return null
    default:
      return placeholderForFormat(resolved.format)
  }
}

function placeholderForFormat(format?: string): string {
  switch (format) {
    case 'date-time':
      return '2026-01-01T00:00:00Z'
    case 'date':
      return '2026-01-01'
    case 'email':
      return 'admin@example.com'
    case 'uuid':
      return '00000000-0000-0000-0000-000000000000'
    default:
      return ''
  }
}

/** The default value a query field should start with, as a string. */
export function defaultValueFor(
  document: OpenApiDocument | null,
  schema: OpenApiSchema | undefined,
): string {
  const resolved = resolveSchema(document, unwrapNullable(resolveSchema(document, schema)).schema)
  const value = resolved?.default ?? resolved?.example
  if (value === undefined || value === null) return ''
  return typeof value === 'object' ? JSON.stringify(value) : String(value)
}

/** Enum options for a query field, so common filters become a select. */
export function enumOptionsFor(
  document: OpenApiDocument | null,
  schema: OpenApiSchema | undefined,
): string[] {
  const resolved = resolveSchema(document, unwrapNullable(resolveSchema(document, schema)).schema)
  return (resolved?.enum ?? []).map((value) => String(value))
}
