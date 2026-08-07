import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { ApiError } from '@/infra/http'

import { openApiService } from '../services/openapi.service'
import type { OpenApiDocument, Operation } from '../types'
import { groupByTag, matchesQuery, toOperations } from '../utils/operations'

export const useExplorerStore = defineStore('explorer', () => {
  const document = ref<OpenApiDocument | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const loadedAt = ref<string | null>(null)

  // Filters.
  const query = ref('')
  const tag = ref<string | null>(null)
  // The console exists for the guarded surface, so that is the default view.
  const panelOnly = ref(true)

  const operations = computed(() => toOperations(document.value))

  const scoped = computed(() =>
    panelOnly.value ? operations.value.filter((item) => item.isPanel) : operations.value,
  )

  const tags = computed(() => {
    const counts = new Map<string, number>()
    for (const operation of scoped.value) {
      counts.set(operation.tag, (counts.get(operation.tag) ?? 0) + 1)
    }
    return [...counts.entries()]
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => a.name.localeCompare(b.name))
  })

  const filtered = computed(() =>
    scoped.value.filter(
      (operation) =>
        (!tag.value || operation.tag === tag.value) && matchesQuery(operation, query.value),
    ),
  )

  const groups = computed(() => groupByTag(filtered.value))

  const stats = computed(() => ({
    total: operations.value.length,
    panel: operations.value.filter((item) => item.isPanel).length,
    shown: filtered.value.length,
  }))

  async function load(force = false): Promise<void> {
    if (loading.value) return
    if (document.value && !force) return
    loading.value = true
    error.value = null
    try {
      document.value = await openApiService.load()
      loadedAt.value = new Date().toISOString()
    } catch (cause) {
      error.value = cause instanceof ApiError ? cause.message : 'The contract could not be loaded.'
    } finally {
      loading.value = false
    }
  }

  function reset(): void {
    query.value = ''
    tag.value = null
  }

  function find(id: string): Operation | undefined {
    return operations.value.find((operation) => operation.id === id)
  }

  return {
    document,
    loading,
    error,
    loadedAt,
    query,
    tag,
    panelOnly,
    operations,
    tags,
    filtered,
    groups,
    stats,
    load,
    reset,
    find,
  }
})
