import {
  HTTP_METHODS,
  type GuardLevel,
  type OpenApiDocument,
  type OpenApiParameter,
  type Operation,
} from '../types'

/**
 * The contract carries no `security` block — the backend's guards read the
 * Authorization header directly instead of declaring a FastAPI scheme. So the
 * level is read off the prefix, which is exactly how the routers are wired:
 * `/panel/admins` sits behind `super_admin_required`, the rest of `/panel`
 * behind `admin_required`.
 */
export function guardFor(path: string): GuardLevel {
  if (path.startsWith('/panel/admins')) return 'super-admin'
  if (path.startsWith('/panel/')) return 'admin'
  return 'public'
}

/** Path params FastAPI declares are already listed; a hand-written path may not be. */
function inferPathParams(path: string, declared: OpenApiParameter[]): OpenApiParameter[] {
  return [...path.matchAll(/\{([^}]+)\}/g)]
    .map((match) => match[1])
    .filter(
      (name): name is string =>
        Boolean(name) &&
        !declared.some((parameter) => parameter.in === 'path' && parameter.name === name),
    )
    .map((name) => ({ name, in: 'path', required: true, schema: { type: 'string' } }))
}

/** Flattens `paths` into one entry per method, the shape the explorer lists. */
export function toOperations(document: OpenApiDocument | null): Operation[] {
  if (!document?.paths) return []

  return Object.entries(document.paths).flatMap(([path, item]) =>
    HTTP_METHODS.flatMap((method) => {
      const raw = item[method]
      if (!raw) return []

      // Path-level parameters apply to every method on that path.
      const declared = [...(item.parameters ?? []), ...(raw.parameters ?? [])]
      const parameters = [...inferPathParams(path, declared), ...declared]

      return [
        {
          id: `${method}:${path}`,
          method,
          path,
          tag: raw.tags?.[0] ?? 'Other',
          summary: raw.summary ?? raw.operationId ?? path,
          description: raw.description,
          deprecated: raw.deprecated === true,
          parameters,
          requestBody: raw.requestBody,
          guard: guardFor(path),
          isPanel: path.startsWith('/panel/') || path === '/panel',
        } satisfies Operation,
      ]
    }),
  )
}

/** Case-insensitive match across the fields an operator would type. */
export function matchesQuery(operation: Operation, query: string): boolean {
  const needle = query.trim().toLowerCase()
  if (!needle) return true
  return (
    operation.path.toLowerCase().includes(needle) ||
    operation.method.includes(needle) ||
    operation.summary.toLowerCase().includes(needle) ||
    operation.tag.toLowerCase().includes(needle)
  )
}

/** Groups by tag, tags sorted alphabetically, operations by path then method. */
export function groupByTag(operations: Operation[]): { tag: string; operations: Operation[] }[] {
  const groups = new Map<string, Operation[]>()
  for (const operation of operations) {
    const bucket = groups.get(operation.tag)
    if (bucket) bucket.push(operation)
    else groups.set(operation.tag, [operation])
  }
  return [...groups.entries()]
    .map(([tag, items]) => ({
      tag,
      operations: items.sort(
        (a, b) => a.path.localeCompare(b.path) || a.method.localeCompare(b.method),
      ),
    }))
    .sort((a, b) => a.tag.localeCompare(b.tag))
}
