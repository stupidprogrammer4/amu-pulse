<script setup lang="ts">
import { CircleAlert, RefreshCw } from '@/common/icons'

defineProps<{ message: string; retrying?: boolean }>()
const emit = defineEmits<{ retry: [] }>()
</script>

<template>
  <div
    class="flex flex-wrap items-center gap-3 rounded-xl border border-signal-error/35 bg-signal-error/10 px-4 py-3"
  >
    <CircleAlert :size="17" class="shrink-0 text-signal-error" />
    <p class="min-w-0 flex-1 text-[0.68rem] text-signal-error">{{ message }}</p>
    <button
      type="button"
      :disabled="retrying"
      class="flex h-8 items-center gap-1.5 rounded-lg border border-signal-error/40 px-3 text-[0.62rem] font-semibold text-signal-error transition hover:bg-signal-error/15 disabled:opacity-50"
      @click="emit('retry')"
    >
      <RefreshCw :size="13" :class="retrying && 'animate-spin'" />
      Retry
    </button>
  </div>
</template>
