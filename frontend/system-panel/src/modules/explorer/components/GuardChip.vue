<script setup lang="ts">
import { computed } from 'vue'

import { Globe, Lock, ShieldCheck } from '@/common/icons'

import type { GuardLevel } from '../types'

const props = defineProps<{ guard: GuardLevel; label?: boolean }>()

const config = computed(() => {
  if (props.guard === 'super-admin') {
    return { icon: ShieldCheck, text: 'super admin', tone: 'text-signal-warn' }
  }
  if (props.guard === 'admin') return { icon: Lock, text: 'admin', tone: 'text-accent-300' }
  return { icon: Globe, text: 'public', tone: 'text-content-500' }
})
</script>

<template>
  <span
    class="inline-flex items-center gap-1 font-mono text-[0.52rem]"
    :class="config.tone"
    :title="`Guard inferred from the path prefix: ${config.text}`"
  >
    <component :is="config.icon" :size="12" />
    <span v-if="props.label">{{ config.text }}</span>
  </span>
</template>
