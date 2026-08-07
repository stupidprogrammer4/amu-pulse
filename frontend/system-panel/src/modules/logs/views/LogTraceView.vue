<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { RouterLink } from 'vue-router'

import BaseSpinner from '@/common/components/BaseSpinner.vue'
import EmptyState from '@/common/components/EmptyState.vue'
import ErrorState from '@/common/components/ErrorState.vue'
import { Check, ChevronLeft, Clipboard } from '@/common/icons'
import { formatDateTime, formatMillis, formatRelative } from '@/common/utils/format'
import { ApiError } from '@/infra/http'

import LogDetailDrawer from '../components/LogDetailDrawer.vue'
import LogLevelChip from '../components/LogLevelChip.vue'
import { logsService } from '../services/logs.service'
import type { LogOut } from '../types'

const route = useRoute()
const requestId = computed(() => String(route.params.requestId ?? ''))

const entries = ref<LogOut[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const inspected = ref<LogOut | null>(null)
const copied = ref(false)

/** The whole point of a trace is the order things happened in. */
const ordered = computed(() =>
  [...entries.value].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
  ),
)

const span = computed(() => {
  if (ordered.value.length < 2) return null
  const first = new Date(ordered.value[0].timestamp).getTime()
  const last = new Date(ordered.value[ordered.value.length - 1].timestamp).getTime()
  return Number.isFinite(first) && Number.isFinite(last) ? last - first : null
})

/** Milliseconds since the first line, so the slow step is obvious. */
function offset(entry: LogOut): string {
  if (!ordered.value.length) return ''
  const base = new Date(ordered.value[0].timestamp).getTime()
  const delta = new Date(entry.timestamp).getTime() - base
  return Number.isFinite(delta) ? `+${delta.toLocaleString('en-US')} ms` : ''
}

async function load(): Promise<void> {
  if (!requestId.value) return
  loading.value = true
  error.value = null
  try {
    entries.value = await logsService.trace(requestId.value)
  } catch (cause) {
    error.value = cause instanceof ApiError ? cause.message : 'The trace could not be read.'
    entries.value = []
  } finally {
    loading.value = false
  }
}

async function copyId(): Promise<void> {
  await navigator.clipboard.writeText(requestId.value)
  copied.value = true
  window.setTimeout(() => (copied.value = false), 1600)
}

watch(requestId, load, { immediate: true })
</script>

<template>
  <div>
    <RouterLink
      :to="{ name: 'logs' }"
      class="mb-4 inline-flex items-center gap-1.5 text-[0.66rem] text-content-400 transition hover:text-content-100"
    >
      <ChevronLeft :size="14" />
      Back to logs
    </RouterLink>

    <header class="mb-5">
      <span class="font-mono text-[0.58rem] font-semibold tracking-[0.13em] text-accent-400">
        TRACE
      </span>
      <div class="mt-2 flex flex-wrap items-center gap-3">
        <h1 class="font-mono text-2xl font-extrabold tracking-[-0.03em] break-all text-content-100">
          {{ requestId }}
        </h1>
        <button
          type="button"
          class="flex h-8 items-center gap-1.5 rounded-lg border border-line px-2.5 text-[0.62rem] text-content-400 transition hover:text-content-100"
          @click="copyId"
        >
          <Check v-if="copied" :size="12" class="text-signal-ok" />
          <Clipboard v-else :size="12" />
          {{ copied ? 'Copied' : 'Copy id' }}
        </button>
      </div>
      <p class="mt-2 text-[0.72rem] text-content-400">
        {{ ordered.length }} line{{ ordered.length === 1 ? '' : 's' }}
        <template v-if="span !== null"> over {{ span.toLocaleString('en-US') }} ms</template>
        <template v-if="ordered.length">
          · started {{ formatRelative(ordered[0].timestamp) }}
        </template>
      </p>
    </header>

    <ErrorState v-if="error" :message="error" :retrying="loading" @retry="load" />

    <div v-else-if="loading" class="grid place-items-center py-16">
      <BaseSpinner label="Reading the trace" />
    </div>

    <EmptyState
      v-else-if="!ordered.length"
      icon="Waypoints"
      title="No lines under this request id"
      body="Elasticsearch has nothing filed against it — the id may be from a retention window that has already rolled off."
    />

    <ol v-else class="relative grid gap-2 border-l border-line pl-5">
      <li
        v-for="(entry, index) in ordered"
        :key="`${entry.timestamp}-${index}`"
        class="relative cursor-pointer rounded-xl border border-line bg-surface-800 px-4 py-3 transition hover:border-line-strong"
        @click="inspected = entry"
      >
        <span
          class="absolute top-5 -left-[1.6rem] size-2 rounded-full ring-4 ring-surface-950"
          :class="entry.error ? 'bg-signal-error' : 'bg-accent-500'"
        />
        <div class="flex flex-wrap items-center gap-x-3 gap-y-1.5">
          <LogLevelChip :level="entry.log?.level" />
          <span class="font-mono text-[0.6rem] text-content-400">
            {{ formatDateTime(entry.timestamp) }}{{ formatMillis(entry.timestamp) }}
          </span>
          <span class="font-mono text-[0.58rem] text-accent-400">{{ offset(entry) }}</span>
          <span class="ml-auto font-mono text-[0.56rem] text-content-500">
            {{ entry.container?.name ?? entry.service?.name ?? '' }}
          </span>
        </div>
        <p class="mt-2 text-[0.7rem] leading-relaxed text-content-200">
          {{ entry.message || entry.error?.message || '—' }}
        </p>
        <p v-if="entry.log?.logger" class="mt-1 font-mono text-[0.55rem] text-content-500">
          {{ entry.log.logger }}
        </p>
      </li>
    </ol>

    <LogDetailDrawer v-if="inspected" :entry="inspected" @close="inspected = null" />
  </div>
</template>
