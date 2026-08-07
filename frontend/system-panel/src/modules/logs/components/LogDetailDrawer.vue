<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { Check, Clipboard, Waypoints, X } from '@/common/icons'
import { formatDateTime, formatMillis, formatRelative } from '@/common/utils/format'

import type { LogOut } from '../types'
import LogLevelChip from './LogLevelChip.vue'

const props = defineProps<{ entry: LogOut }>()
const emit = defineEmits<{ close: [] }>()

const copied = ref(false)

const facts = computed(() => {
  const origin = props.entry.log?.origin
  const file = origin?.file
  return [
    { label: 'Timestamp', value: `${formatDateTime(props.entry.timestamp)}${formatMillis(props.entry.timestamp)}` },
    { label: 'Age', value: formatRelative(props.entry.timestamp) },
    { label: 'Container', value: props.entry.container?.name },
    { label: 'Service', value: props.entry.service?.name },
    { label: 'Logger', value: props.entry.log?.logger },
    { label: 'Stream', value: props.entry.stream },
    { label: 'Function', value: origin?.function },
    {
      label: 'Origin',
      value: file?.path ?? file?.name ? `${file?.path ?? file?.name}${file?.line ? `:${file.line}` : ''}` : null,
    },
  ].filter((fact) => fact.value)
})

async function copyRecord(): Promise<void> {
  await navigator.clipboard.writeText(JSON.stringify(props.entry, null, 2))
  copied.value = true
  window.setTimeout(() => (copied.value = false), 1600)
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex justify-end">
    <div class="absolute inset-0 bg-black/65 backdrop-blur-[2px]" @click="emit('close')" />

    <aside
      class="relative flex h-full w-full max-w-2xl flex-col border-l border-line bg-surface-900 shadow-2xl"
      role="dialog"
      aria-label="Log entry"
    >
      <header class="flex items-start gap-3 border-b border-line px-5 py-4">
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <LogLevelChip :level="entry.log?.level" />
            <span class="font-mono text-[0.62rem] text-content-400">
              {{ formatDateTime(entry.timestamp) }}{{ formatMillis(entry.timestamp) }}
            </span>
          </div>
          <p class="mt-2 text-[0.78rem] leading-relaxed font-semibold text-content-100">
            {{ entry.message || entry.error?.message || 'No message' }}
          </p>
        </div>
        <button
          type="button"
          class="grid size-8 shrink-0 place-items-center rounded-lg border border-line text-content-400 transition hover:text-content-100"
          aria-label="Close"
          @click="emit('close')"
        >
          <X :size="15" />
        </button>
      </header>

      <div class="flex-1 overflow-y-auto px-5 py-4">
        <dl class="grid gap-x-6 gap-y-2.5 sm:grid-cols-2">
          <div v-for="fact in facts" :key="fact.label" class="min-w-0">
            <dt class="text-[0.55rem] tracking-[0.12em] text-content-500 uppercase">
              {{ fact.label }}
            </dt>
            <dd class="mt-0.5 truncate font-mono text-[0.66rem] text-content-200">
              {{ fact.value }}
            </dd>
          </div>
        </dl>

        <RouterLink
          v-if="entry.request_id"
          :to="{ name: 'log-trace', params: { requestId: entry.request_id } }"
          class="mt-5 flex items-center gap-2 rounded-xl border border-line bg-surface-850 px-3.5 py-3 transition hover:border-accent-500/50"
          @click="emit('close')"
        >
          <Waypoints :size="15" class="text-accent-400" />
          <div class="min-w-0 flex-1">
            <strong class="block text-[0.66rem] font-semibold text-content-100">
              Open the full trace
            </strong>
            <small class="block truncate font-mono text-[0.56rem] text-content-500">
              {{ entry.request_id }}
            </small>
          </div>
        </RouterLink>

        <template v-if="entry.error">
          <h3 class="mt-6 mb-2 text-[0.58rem] font-bold tracking-[0.12em] text-content-500 uppercase">
            Error
          </h3>
          <div class="rounded-xl border border-signal-error/30 bg-signal-error/8 p-3.5">
            <p v-if="entry.error.type" class="font-mono text-[0.66rem] font-bold text-signal-error">
              {{ entry.error.type }}
            </p>
            <p v-if="entry.error.message" class="mt-1 text-[0.66rem] text-content-200">
              {{ entry.error.message }}
            </p>
            <pre
              v-if="entry.error.stack_trace"
              class="mt-3 max-h-80 overflow-auto rounded-lg bg-surface-950 p-3 font-mono text-[0.58rem] leading-relaxed whitespace-pre text-content-300"
            >{{ entry.error.stack_trace }}</pre>
          </div>
        </template>

        <h3 class="mt-6 mb-2 text-[0.58rem] font-bold tracking-[0.12em] text-content-500 uppercase">
          Raw record
        </h3>
        <pre
          class="max-h-80 overflow-auto rounded-xl border border-line bg-surface-950 p-3.5 font-mono text-[0.58rem] leading-relaxed text-content-300"
        >{{ JSON.stringify(entry, null, 2) }}</pre>
      </div>

      <footer class="border-t border-line px-5 py-3">
        <button
          type="button"
          class="flex h-9 items-center gap-2 rounded-lg border border-line px-3.5 text-[0.66rem] text-content-300 transition hover:border-line-strong hover:text-content-100"
          @click="copyRecord"
        >
          <Check v-if="copied" :size="13" class="text-signal-ok" />
          <Clipboard v-else :size="13" />
          {{ copied ? 'Copied' : 'Copy record' }}
        </button>
      </footer>
    </aside>
  </div>
</template>
