<script setup lang="ts">
import { computed } from 'vue'

import type { HttpMethod } from '../types'

const props = defineProps<{ method: HttpMethod }>()

// Each verb keeps one colour across the list, the drawer and the response box.
const palette: Record<string, string> = {
  get: 'bg-accent-500/14 text-accent-300',
  post: 'bg-signal-ok/14 text-signal-ok',
  put: 'bg-signal-warn/14 text-signal-warn',
  patch: 'bg-signal-warn/14 text-signal-warn',
  delete: 'bg-signal-error/14 text-signal-error',
}

const tone = computed(() => palette[props.method] ?? 'bg-surface-700 text-content-400')
</script>

<template>
  <span
    class="inline-grid h-5 min-w-14 place-items-center rounded font-mono text-[0.52rem] font-bold uppercase"
    :class="tone"
  >
    {{ props.method }}
  </span>
</template>
