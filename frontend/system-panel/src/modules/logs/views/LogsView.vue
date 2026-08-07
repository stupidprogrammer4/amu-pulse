<script setup lang="ts">
import { onMounted, ref } from 'vue'

import BaseSpinner from '@/common/components/BaseSpinner.vue'
import EmptyState from '@/common/components/EmptyState.vue'
import ErrorState from '@/common/components/ErrorState.vue'
import PagerBar from '@/common/components/PagerBar.vue'
import { RefreshCw } from '@/common/icons'
import { formatNumber, formatRelative } from '@/common/utils/format'

import LogDetailDrawer from '../components/LogDetailDrawer.vue'
import LogFilters from '../components/LogFilters.vue'
import LogTable from '../components/LogTable.vue'
import LogVolumeChart from '../components/LogVolumeChart.vue'
import { useLogsStore } from '../stores/logs.store'
import type { LogOut } from '../types'

const logs = useLogsStore()
const inspected = ref<LogOut | null>(null)

onMounted(() => {
  if (!logs.loadedAt) void logs.load()
})
</script>

<template>
  <div>
    <header class="mb-5 flex flex-wrap items-end gap-x-4 gap-y-2">
      <div class="mr-auto">
        <span class="font-mono text-[0.58rem] font-semibold tracking-[0.13em] text-accent-400">
          OPERATIONS
        </span>
        <h1 class="mt-2 text-3xl font-extrabold tracking-[-0.045em] text-content-100">Logs</h1>
        <p class="mt-2 text-[0.76rem] text-content-400">
          Everything the backend ships to Elasticsearch, searchable, with the full trace behind a
          request id.
        </p>
      </div>

      <div class="flex items-center gap-3">
        <small v-if="logs.loadedAt" class="font-mono text-[0.58rem] text-content-500">
          read {{ formatRelative(logs.loadedAt) }}
        </small>
        <button
          type="button"
          :disabled="logs.loading"
          class="flex h-9 items-center gap-1.5 rounded-lg border border-line px-3 text-[0.66rem] text-content-300 transition hover:border-line-strong hover:text-content-100 disabled:opacity-50"
          @click="logs.load()"
        >
          <RefreshCw :size="13" :class="logs.loading && 'animate-spin'" />
          Refresh
        </button>
      </div>
    </header>

    <div class="grid gap-4">
      <LogVolumeChart />

      <LogFilters />

      <section class="overflow-hidden rounded-2xl border border-line bg-surface-800">
        <header class="flex items-center justify-between gap-4 border-b border-line px-4 py-3">
          <div>
            <h2 class="text-[0.76rem] font-bold text-content-100">Log index</h2>
            <p class="mt-0.5 text-[0.6rem] text-content-400">
              <code class="font-mono">/panel/logs</code> ·
              {{ formatNumber(logs.pager?.total_items ?? 0) }} matching lines
            </p>
          </div>
          <BaseSpinner v-if="logs.loading && logs.entries.length" label="Reading" :size="15" />
        </header>

        <ErrorState
          v-if="logs.error"
          class="m-4"
          :message="logs.error"
          :retrying="logs.loading"
          @retry="logs.load()"
        />

        <div v-else-if="logs.loading && !logs.entries.length" class="grid place-items-center py-16">
          <BaseSpinner label="Reading the log index" />
        </div>

        <EmptyState
          v-else-if="!logs.entries.length"
          title="No lines match"
          body="Nothing in Elasticsearch answers this query. Widen the range or clear a filter."
        />

        <template v-else>
          <LogTable :entries="logs.entries" :busy="logs.loading" @inspect="inspected = $event" />
          <PagerBar
            :pager="logs.pager"
            :page="logs.page"
            :per-page="logs.perPage"
            :busy="logs.loading"
            @update:page="logs.goToPage($event)"
            @update:per-page="logs.setPerPage($event)"
          />
        </template>
      </section>
    </div>

    <LogDetailDrawer v-if="inspected" :entry="inspected" @close="inspected = null" />
  </div>
</template>
