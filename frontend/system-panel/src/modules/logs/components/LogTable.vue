<script setup lang="ts">
import { RouterLink } from 'vue-router'

import { Waypoints } from '@/common/icons'
import { formatDateTime, formatMillis } from '@/common/utils/format'

import type { LogOut } from '../types'
import LogLevelChip from './LogLevelChip.vue'

defineProps<{ entries: LogOut[]; busy?: boolean }>()
const emit = defineEmits<{ inspect: [LogOut] }>()
</script>

<template>
  <div class="overflow-x-auto" :class="busy && 'opacity-55'">
    <table class="w-full min-w-[54rem] border-collapse text-left">
      <thead>
        <tr class="border-b border-line text-[0.55rem] tracking-[0.12em] text-content-500 uppercase">
          <th class="px-4 py-2.5 font-bold">Time</th>
          <th class="px-3 py-2.5 font-bold">Level</th>
          <th class="px-3 py-2.5 font-bold">Container</th>
          <th class="px-3 py-2.5 font-bold">Message</th>
          <th class="px-3 py-2.5 font-bold">Trace</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(entry, index) in entries"
          :key="`${entry.timestamp}-${index}`"
          class="cursor-pointer border-b border-line/60 align-top transition last:border-0 hover:bg-surface-700/60"
          @click="emit('inspect', entry)"
        >
          <td class="px-4 py-2.5 font-mono text-[0.62rem] whitespace-nowrap text-content-300">
            {{ formatDateTime(entry.timestamp) }}<span class="text-content-500">{{
              formatMillis(entry.timestamp)
            }}</span>
          </td>
          <td class="px-3 py-2.5">
            <LogLevelChip :level="entry.log?.level" />
          </td>
          <td class="px-3 py-2.5">
            <span class="block font-mono text-[0.62rem] text-content-200">
              {{ entry.container?.name ?? '—' }}
            </span>
            <span class="mt-0.5 block truncate font-mono text-[0.55rem] text-content-500">
              {{ entry.log?.logger ?? entry.service?.name ?? '' }}
            </span>
          </td>
          <td class="max-w-0 px-3 py-2.5">
            <p class="truncate text-[0.66rem] text-content-200">
              {{ entry.message || entry.error?.message || '—' }}
            </p>
            <p v-if="entry.error?.type" class="mt-0.5 truncate font-mono text-[0.56rem] text-signal-error">
              {{ entry.error.type }}
            </p>
          </td>
          <td class="px-3 py-2.5">
            <RouterLink
              v-if="entry.request_id"
              :to="{ name: 'log-trace', params: { requestId: entry.request_id } }"
              class="inline-flex items-center gap-1 rounded-md border border-line px-1.5 py-1 font-mono text-[0.55rem] text-content-400 transition hover:border-accent-500/60 hover:text-accent-300"
              :title="entry.request_id"
              @click.stop
            >
              <Waypoints :size="11" />
              {{ entry.request_id.slice(0, 8) }}
            </RouterLink>
            <span v-else class="font-mono text-[0.55rem] text-content-500">—</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
