<script setup lang="ts">
import { computed } from 'vue'

import { Bug, CircleX, Info, OctagonAlert, TriangleAlert } from '@/common/icons'

/**
 * Level is a status, so it never travels as colour alone: every chip carries its
 * word and its own glyph. Critical shares error's red and separates on fill —
 * solid rather than tinted — because a sixth distinguishable hue on this surface
 * would fail the contrast floor.
 */
const props = withDefaults(defineProps<{ level?: string | null; compact?: boolean }>(), {
  level: null,
  compact: false,
})

const styles: Record<string, { icon: typeof Info; klass: string }> = {
  debug: { icon: Bug, klass: 'border-content-500/40 bg-content-500/10 text-content-400' },
  info: { icon: Info, klass: 'border-content-300/30 bg-content-300/10 text-content-200' },
  warning: {
    icon: TriangleAlert,
    klass: 'border-signal-warn/45 bg-signal-warn/12 text-signal-warn',
  },
  error: { icon: CircleX, klass: 'border-signal-error/45 bg-signal-error/12 text-signal-error' },
  critical: {
    icon: OctagonAlert,
    klass: 'border-signal-error bg-signal-error text-surface-950 font-bold',
  },
}

const normalized = computed(() => (props.level ?? '').toLowerCase())
const style = computed(
  () =>
    styles[normalized.value] ?? {
      icon: Info,
      klass: 'border-line-strong bg-surface-700 text-content-400',
    },
)
</script>

<template>
  <span
    class="inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 font-mono text-[0.55rem] font-semibold tracking-wide uppercase"
    :class="style.klass"
  >
    <component :is="style.icon" :size="11" :stroke-width="2.2" />
    <span v-if="!compact">{{ normalized || 'unknown' }}</span>
  </span>
</template>
