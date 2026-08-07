<script setup lang="ts">
import { computed } from 'vue'

import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from '@/common/icons'
import type { PagerMeta } from '@/infra/http'

/**
 * The backend's pager reports totals and the two edge flags but never echoes the
 * page the caller asked for, so `page` and `perPage` come from the store that
 * sent them.
 */
const props = defineProps<{
  pager: PagerMeta | null
  page: number
  perPage: number
  busy?: boolean
}>()

const emit = defineEmits<{ 'update:page': [number]; 'update:perPage': [number] }>()

const perPageOptions = [20, 50, 100]

const range = computed(() => {
  const total = props.pager?.total_items ?? 0
  if (!total) return null
  const first = (props.page - 1) * props.perPage + 1
  return { first, last: Math.min(first + props.perPage - 1, total), total }
})

const lastPage = computed(() => Math.max(props.pager?.total_pages ?? 1, 1))

function go(page: number): void {
  const target = Math.min(Math.max(page, 1), lastPage.value)
  if (target !== props.page) emit('update:page', target)
}
</script>

<template>
  <div
    class="flex flex-wrap items-center gap-x-4 gap-y-2.5 border-t border-line px-4 py-3 text-[0.62rem] text-content-400"
  >
    <p v-if="range" class="font-mono">
      {{ range.first.toLocaleString('en-US') }}–{{ range.last.toLocaleString('en-US') }} of
      {{ range.total.toLocaleString('en-US') }}
    </p>
    <p v-else class="font-mono">no results</p>

    <label class="flex items-center gap-1.5">
      <span>per page</span>
      <select
        :value="perPage"
        class="h-7 rounded-lg border border-line bg-surface-800 px-1.5 font-mono text-[0.62rem] text-content-200 outline-none focus:border-accent-500"
        @change="emit('update:perPage', Number(($event.target as HTMLSelectElement).value))"
      >
        <option v-for="option in perPageOptions" :key="option" :value="option">{{ option }}</option>
      </select>
    </label>

    <div class="ml-auto flex items-center gap-1">
      <button
        v-for="control in [
          { icon: ChevronsLeft, to: 1, label: 'First page', off: !pager?.has_prev },
          { icon: ChevronLeft, to: page - 1, label: 'Previous page', off: !pager?.has_prev },
        ]"
        :key="control.label"
        type="button"
        :disabled="control.off || busy"
        :aria-label="control.label"
        class="grid size-7 place-items-center rounded-lg border border-line text-content-300 transition hover:border-line-strong hover:text-content-100 disabled:cursor-not-allowed disabled:opacity-35"
        @click="go(control.to)"
      >
        <component :is="control.icon" :size="13" />
      </button>

      <span class="px-2 font-mono text-content-300">{{ page }} / {{ lastPage }}</span>

      <button
        v-for="control in [
          { icon: ChevronRight, to: page + 1, label: 'Next page', off: !pager?.has_next },
          { icon: ChevronsRight, to: lastPage, label: 'Last page', off: !pager?.has_next },
        ]"
        :key="control.label"
        type="button"
        :disabled="control.off || busy"
        :aria-label="control.label"
        class="grid size-7 place-items-center rounded-lg border border-line text-content-300 transition hover:border-line-strong hover:text-content-100 disabled:cursor-not-allowed disabled:opacity-35"
        @click="go(control.to)"
      >
        <component :is="control.icon" :size="13" />
      </button>
    </div>
  </div>
</template>
