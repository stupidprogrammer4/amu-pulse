<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import { ChevronRight, Menu } from '@/common/icons'

const emit = defineEmits<{ toggleNav: [] }>()

const route = useRoute()
const title = computed(() => String(route.meta.title ?? 'Console'))
</script>

<template>
  <header
    class="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-line bg-surface-950/85 px-4 backdrop-blur-md sm:px-6"
  >
    <button
      type="button"
      class="grid size-9 place-items-center rounded-lg border border-line bg-surface-850 text-content-300 lg:hidden"
      aria-label="Open navigation"
      @click="emit('toggleNav')"
    >
      <Menu :size="16" />
    </button>

    <nav class="flex items-center gap-1.5 text-[0.66rem] text-content-400">
      <span>System panel</span>
      <ChevronRight :size="13" class="text-content-500" />
      <strong class="font-semibold text-content-100">{{ title }}</strong>
    </nav>

    <div class="ml-auto flex items-center gap-2 text-[0.6rem] text-content-400">
      <span class="size-1.5 rounded-full bg-signal-ok shadow-[0_0_7px] shadow-signal-ok/70" />
      <span class="hidden font-mono sm:inline">session active</span>
    </div>
  </header>
</template>
