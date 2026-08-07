<script setup lang="ts">
import { RouterLink } from 'vue-router'

import { ChevronRight, CircleAlert } from '@/common/icons'
</script>

<template>
  <div
    class="grid min-h-screen place-content-center justify-items-center bg-surface-950 px-6 text-center"
  >
    <CircleAlert :size="30" class="text-accent-400" />
    <span class="mt-5 font-mono text-[0.58rem] tracking-[0.14em] text-content-500">HTTP 404</span>
    <h1 class="mt-2 text-2xl font-extrabold text-content-100">No route matches that path</h1>
    <p class="mt-1.5 text-[0.72rem] text-content-400">
      The system panel only serves its own console routes.
    </p>
    <RouterLink
      :to="{ name: 'overview' }"
      class="mt-7 flex items-center gap-1.5 rounded-xl bg-accent-500 px-4 py-2.5 text-[0.7rem] font-bold text-surface-950 transition hover:bg-accent-400"
    >
      Back to overview
      <ChevronRight :size="14" />
    </RouterLink>
  </div>
</template>
