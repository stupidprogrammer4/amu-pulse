<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { ListFilter, RotateCcw, Search, X } from '@/common/icons'
import { formatNumber } from '@/common/utils/format'

import { useLogsStore } from '../stores/logs.store'
import { logLevels, type LogLevel } from '../types'

const logs = useLogsStore()

// Text inputs are local until submit so every keystroke is not a query.
const draftQuery = ref(logs.filters.q)
const draftRequestId = ref(logs.filters.requestId)
const draftFrom = ref(logs.filters.fromTime)
const draftTo = ref(logs.filters.toTime)
const expanded = ref(false)

watch(
  () => logs.filters,
  (current) => {
    draftQuery.value = current.q
    draftRequestId.value = current.requestId
    draftFrom.value = current.fromTime
    draftTo.value = current.toTime
  },
  { deep: true },
)

const levelCounts = computed(() => {
  const counts = new Map(logs.levelFacets.map((facet) => [facet.value, facet.count]))
  return logLevels.map((level) => ({ level, count: counts.get(level) ?? 0 }))
})

function submit(): void {
  void logs.apply({
    q: draftQuery.value,
    requestId: draftRequestId.value,
    fromTime: draftFrom.value,
    toTime: draftTo.value,
  })
}

function clearRange(): void {
  draftFrom.value = ''
  draftTo.value = ''
  submit()
}

function toggleLevel(level: LogLevel): void {
  const next = logs.filters.levels.includes(level)
    ? logs.filters.levels.filter((entry) => entry !== level)
    : [...logs.filters.levels, level]
  void logs.apply({ levels: next })
}

function toggleIn(key: 'loggers' | 'containers', value: string): void {
  const current = logs.filters[key]
  const next = current.includes(value)
    ? current.filter((entry) => entry !== value)
    : [...current, value]
  void logs.apply({ [key]: next })
}
</script>

<template>
  <section class="rounded-2xl border border-line bg-surface-800">
    <form class="flex flex-wrap items-center gap-2.5 p-3" @submit.prevent="submit">
      <label class="relative min-w-56 flex-1">
        <Search
          :size="14"
          class="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-content-500"
        />
        <input
          v-model="draftQuery"
          type="search"
          placeholder="Search message text…"
          class="h-9 w-full rounded-lg border border-line bg-surface-850 pr-3 pl-9 text-[0.7rem] text-content-100 outline-none transition placeholder:text-content-500 focus:border-accent-500"
        />
      </label>

      <input
        v-model="draftRequestId"
        type="text"
        spellcheck="false"
        placeholder="request id"
        class="h-9 w-44 rounded-lg border border-line bg-surface-850 px-3 font-mono text-[0.66rem] text-content-100 outline-none transition placeholder:text-content-500 focus:border-accent-500"
      />

      <button
        type="submit"
        class="h-9 rounded-lg bg-accent-500 px-4 text-[0.68rem] font-bold text-surface-950 transition hover:bg-accent-400"
      >
        Search
      </button>

      <button
        type="button"
        class="flex h-9 items-center gap-1.5 rounded-lg border border-line px-3 text-[0.66rem] text-content-300 transition hover:border-line-strong hover:text-content-100"
        :aria-expanded="expanded"
        @click="expanded = !expanded"
      >
        <ListFilter :size="14" />
        Filters
        <span
          v-if="logs.activeFilterCount"
          class="rounded-full bg-accent-500 px-1.5 font-mono text-[0.55rem] font-bold text-surface-950"
        >
          {{ logs.activeFilterCount }}
        </span>
      </button>

      <button
        v-if="logs.activeFilterCount"
        type="button"
        class="flex h-9 items-center gap-1.5 rounded-lg border border-line px-3 text-[0.66rem] text-content-400 transition hover:border-signal-error/50 hover:text-signal-error"
        @click="logs.reset()"
      >
        <RotateCcw :size="13" />
        Clear
      </button>
    </form>

    <div v-if="expanded" class="grid gap-4 border-t border-line p-3.5">
      <div>
        <p class="mb-2 text-[0.58rem] font-bold tracking-[0.12em] text-content-500 uppercase">
          Level
        </p>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="entry in levelCounts"
            :key="entry.level"
            type="button"
            :aria-pressed="logs.filters.levels.includes(entry.level)"
            class="flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 font-mono text-[0.6rem] transition"
            :class="
              logs.filters.levels.includes(entry.level)
                ? 'border-accent-500 bg-accent-500/14 text-accent-300'
                : 'border-line bg-surface-850 text-content-400 hover:border-line-strong hover:text-content-200'
            "
            @click="toggleLevel(entry.level)"
          >
            {{ entry.level }}
            <span class="text-content-500">{{ formatNumber(entry.count) }}</span>
          </button>
        </div>
      </div>

      <div
        v-for="group in [
          { key: 'containers' as const, title: 'Container', facets: logs.containerFacets },
          { key: 'loggers' as const, title: 'Logger', facets: logs.loggerFacets },
        ]"
        :key="group.key"
      >
        <p class="mb-2 text-[0.58rem] font-bold tracking-[0.12em] text-content-500 uppercase">
          {{ group.title }}
        </p>
        <p v-if="!group.facets.length" class="text-[0.62rem] text-content-500">
          Nothing to filter by in the current result set.
        </p>
        <div v-else class="flex max-h-32 flex-wrap gap-1.5 overflow-y-auto">
          <button
            v-for="facet in group.facets"
            :key="facet.value"
            type="button"
            :aria-pressed="logs.filters[group.key].includes(facet.value)"
            class="flex max-w-full items-center gap-1.5 rounded-lg border px-2.5 py-1.5 font-mono text-[0.6rem] transition"
            :class="
              logs.filters[group.key].includes(facet.value)
                ? 'border-accent-500 bg-accent-500/14 text-accent-300'
                : 'border-line bg-surface-850 text-content-400 hover:border-line-strong hover:text-content-200'
            "
            @click="toggleIn(group.key, facet.value)"
          >
            <span class="truncate">{{ facet.value }}</span>
            <span class="shrink-0 text-content-500">{{ formatNumber(facet.count) }}</span>
          </button>
        </div>
      </div>

      <div class="flex flex-wrap gap-3">
        <label
          v-for="bound in [
            { key: 'from' as const, label: 'From' },
            { key: 'to' as const, label: 'To' },
          ]"
          :key="bound.key"
          class="text-[0.58rem] font-bold tracking-[0.12em] text-content-500 uppercase"
        >
          <span class="mb-1.5 block">{{ bound.label }}</span>
          <input
            v-if="bound.key === 'from'"
            v-model="draftFrom"
            type="datetime-local"
            class="h-9 rounded-lg border border-line bg-surface-850 px-2.5 font-mono text-[0.62rem] text-content-200 outline-none focus:border-accent-500"
            @change="submit"
          />
          <input
            v-else
            v-model="draftTo"
            type="datetime-local"
            class="h-9 rounded-lg border border-line bg-surface-850 px-2.5 font-mono text-[0.62rem] text-content-200 outline-none focus:border-accent-500"
            @change="submit"
          />
        </label>

        <button
          v-if="draftFrom || draftTo"
          type="button"
          class="mt-auto flex h-9 items-center gap-1.5 rounded-lg border border-line px-3 text-[0.62rem] text-content-400 transition hover:text-content-100"
          @click="clearRange"
        >
          <X :size="12" />
          Clear range
        </button>
      </div>
    </div>
  </section>
</template>
