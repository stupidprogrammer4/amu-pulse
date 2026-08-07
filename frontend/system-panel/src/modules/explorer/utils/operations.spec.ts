import { describe, expect, it } from 'vitest'

import type { OpenApiDocument } from '../types'
import { groupByTag, guardFor, matchesQuery, toOperations } from './operations'
import { describeSchema, sampleFor } from './schema'

const document: OpenApiDocument = {
  openapi: '3.0.2',
  info: { title: 'AMU Pulse', version: '1.0.0' },
  paths: {
    '/panel/logs': {
      get: { tags: ['Panel Logs'], summary: 'Search logs', parameters: [] },
    },
    '/panel/admins/{id}': {
      // Declared once on the path, shared by both methods.
      parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'integer' } }],
      get: { tags: ['Panel Admins'], summary: 'Get admin' },
      patch: {
        tags: ['Panel Admins'],
        summary: 'Update admin',
        requestBody: {
          required: true,
          content: { 'application/json': { schema: { $ref: '#/components/schemas/AdminUpdate' } } },
        },
      },
    },
    // No declared parameters at all — the path braces are the only clue.
    '/prices/{asset_code}': {
      get: { tags: ['Prices'], summary: 'Public price' },
    },
  },
  components: {
    schemas: {
      AdminUpdate: {
        type: 'object',
        title: 'AdminUpdate',
        required: ['username'],
        properties: {
          username: { type: 'string' },
          is_super_admin: { type: 'boolean', default: false },
          note: { anyOf: [{ type: 'string' }, { type: 'null' }] },
        },
      },
    },
  },
}

describe('toOperations', () => {
  const operations = toOperations(document)

  it('emits one entry per path and method', () => {
    expect(operations.map((operation) => operation.id).sort()).toEqual([
      'get:/panel/admins/{id}',
      'get:/panel/logs',
      'get:/prices/{asset_code}',
      'patch:/panel/admins/{id}',
    ])
  })

  it('carries path-level parameters onto every method', () => {
    const patch = operations.find((operation) => operation.id === 'patch:/panel/admins/{id}')
    expect(patch?.parameters.map((parameter) => parameter.name)).toEqual(['id'])
  })

  it('infers a path parameter the contract never declared', () => {
    const price = operations.find((operation) => operation.id === 'get:/prices/{asset_code}')
    expect(price?.parameters).toEqual([
      { name: 'asset_code', in: 'path', required: true, schema: { type: 'string' } },
    ])
  })

  it('does not duplicate a parameter that was declared', () => {
    const admin = operations.find((operation) => operation.id === 'get:/panel/admins/{id}')
    expect(admin?.parameters).toHaveLength(1)
  })

  it('flags the guarded panel surface', () => {
    expect(operations.filter((operation) => operation.isPanel)).toHaveLength(3)
  })

  it('survives a missing document', () => {
    expect(toOperations(null)).toEqual([])
  })
})

describe('guardFor', () => {
  it('reads the level off the prefix the routers use', () => {
    expect(guardFor('/panel/admins')).toBe('super-admin')
    expect(guardFor('/panel/admins/12/username')).toBe('super-admin')
    expect(guardFor('/panel/logs')).toBe('admin')
    expect(guardFor('/prices/gold')).toBe('public')
  })
})

describe('matchesQuery', () => {
  const operation = toOperations(document).find((entry) => entry.id === 'patch:/panel/admins/{id}')!

  it('treats an empty needle as "everything"', () => {
    expect(matchesQuery(operation, '  ')).toBe(true)
  })

  it('matches on path, method, tag and summary, case-insensitively', () => {
    expect(matchesQuery(operation, 'ADMINS/{ID}')).toBe(true)
    expect(matchesQuery(operation, 'patch')).toBe(true)
    expect(matchesQuery(operation, 'Panel Admins')).toBe(true)
    expect(matchesQuery(operation, 'update ADMIN')).toBe(true)
  })

  it('is a substring match, not a fuzzy one — word order counts', () => {
    expect(matchesQuery(operation, 'admins panel')).toBe(false)
  })

  it('rejects a needle that appears nowhere', () => {
    expect(matchesQuery(operation, 'nothing-like-this')).toBe(false)
  })
})

describe('groupByTag', () => {
  it('sorts tags and the operations inside them', () => {
    const groups = groupByTag(toOperations(document))
    expect(groups.map((group) => group.tag)).toEqual(['Panel Admins', 'Panel Logs', 'Prices'])
    expect(groups[0]?.operations.map((operation) => operation.method)).toEqual(['get', 'patch'])
  })
})

describe('schema helpers', () => {
  it('follows a $ref when building a sample body', () => {
    expect(sampleFor(document, { $ref: '#/components/schemas/AdminUpdate' })).toEqual({
      username: '',
      is_super_admin: false,
      note: '',
    })
  })

  it('unwraps the anyOf pydantic writes for an optional field', () => {
    expect(describeSchema(document, { anyOf: [{ type: 'string' }, { type: 'null' }] })).toBe(
      'string | null',
    )
  })

  it('labels enums and arrays', () => {
    expect(describeSchema(document, { type: 'array', items: { type: 'integer' } })).toBe(
      'integer[]',
    )
    expect(describeSchema(document, { enum: ['asc', 'desc'] })).toBe('asc | desc')
  })
})
