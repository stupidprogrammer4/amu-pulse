<script setup lang="ts">
import { RouterLink } from 'vue-router'

import { bootNavigation } from '@/core/bootstrap'

// Built from the modules' own route metadata, so a new module shows up in the
// nav without this file being touched.
const navItems = bootNavigation()
</script>

<template>
  <header class="border-b border-line bg-surface-raised">
    <div class="mx-auto flex max-w-6xl items-center justify-between gap-6 px-4 py-4">
      <RouterLink :to="{ name: 'dashboard' }" class="flex items-center gap-2">
        <span class="text-lg font-bold text-slate-800">نبض طلا</span>
        <span class="rounded-md bg-amber-100 px-2 py-0.5 text-[11px] text-amber-700">بتا</span>
      </RouterLink>

      <nav class="flex items-center gap-1 text-sm">
        <RouterLink
          v-for="item in navItems"
          :key="item.name"
          :to="{ name: item.name }"
          class="rounded-lg px-3 py-1.5 text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
          active-class="bg-slate-900 text-white hover:bg-slate-900 hover:text-white"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </div>
  </header>
</template>
