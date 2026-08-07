<script setup lang="ts">
import { RouterLink } from 'vue-router'

import BrandMark from '@/common/components/BrandMark.vue'
import AppIcon from '@/common/components/AppIcon.vue'
import { LogOut, X } from '@/common/icons'
import { env } from '@/core/config/env'
import { navigation } from '@/core/navigation'
import { useAuthStore } from '@/modules/auth/stores/auth.store'

defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: []; signOut: [] }>()

const auth = useAuthStore()
const isProduction = env.environment === 'production'
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-40 bg-black/60 backdrop-blur-[2px] lg:hidden"
    @click="emit('close')"
  />

  <aside
    class="fixed inset-y-0 left-0 z-50 flex w-68 flex-col border-r border-line bg-surface-900 transition-transform duration-200 lg:translate-x-0"
    :class="open ? 'translate-x-0' : '-translate-x-full'"
  >
    <div class="flex h-16 items-center gap-3 px-4">
      <BrandMark :size="36" />
      <div class="min-w-0">
        <strong class="block truncate text-[0.8rem] font-bold tracking-tight text-content-100">
          AMU Pulse
        </strong>
        <small class="block font-mono text-[0.55rem] tracking-[0.16em] text-content-500">
          SYSTEM PANEL
        </small>
      </div>
      <button
        type="button"
        class="ml-auto grid size-8 place-items-center rounded-lg text-content-400 hover:text-content-100 lg:hidden"
        aria-label="Close navigation"
        @click="emit('close')"
      >
        <X :size="16" />
      </button>
    </div>

    <div
      class="mx-4 mb-4 flex items-center gap-2.5 rounded-xl border border-line bg-surface-850 px-3 py-2.5"
    >
      <span
        class="size-2 rounded-full"
        :class="
          isProduction
            ? 'bg-signal-error shadow-[0_0_8px] shadow-signal-error'
            : 'bg-accent-400 shadow-[0_0_8px] shadow-accent-400'
        "
      />
      <div class="min-w-0">
        <strong class="block text-[0.66rem] font-semibold text-content-100">
          {{ env.environment }}
        </strong>
        <small class="block truncate font-mono text-[0.55rem] text-content-500">
          {{ env.apiBaseUrl }}
        </small>
      </div>
    </div>

    <nav class="flex-1 overflow-y-auto px-3 pb-4">
      <template v-for="section in navigation" :key="section.title">
        <p
          class="mt-4 mb-1.5 px-2 text-[0.55rem] font-bold tracking-[0.14em] text-content-500 uppercase"
        >
          {{ section.title }}
        </p>
        <template v-for="item in section.items" :key="item.label">
          <RouterLink
            v-if="item.ready && item.to"
            :to="{ name: item.to }"
            class="mb-0.5 flex h-10 items-center gap-2.5 rounded-lg px-2.5 text-[0.72rem] text-content-300 transition hover:bg-surface-700 hover:text-content-100"
            active-class="bg-accent-500/14! text-accent-300! shadow-[inset_0_0_0_1px] shadow-accent-500/20"
            @click="emit('close')"
          >
            <AppIcon :name="item.icon" :size="16" />
            <span class="truncate">{{ item.label }}</span>
          </RouterLink>

          <div
            v-else
            class="mb-0.5 flex h-10 cursor-not-allowed items-center gap-2.5 rounded-lg px-2.5 text-[0.72rem] text-content-500"
            :title="`${item.endpoint ?? item.label} — not wired up yet`"
          >
            <AppIcon :name="item.icon" :size="16" />
            <span class="truncate">{{ item.label }}</span>
            <span
              class="ml-auto rounded-full bg-surface-700 px-1.5 py-px font-mono text-[0.5rem] text-content-500"
            >
              {{ item.superAdminOnly ? 'SU' : 'soon' }}
            </span>
          </div>
        </template>
      </template>
    </nav>

    <div class="flex items-center gap-2.5 border-t border-line px-4 py-3">
      <span
        class="grid size-8 shrink-0 place-items-center rounded-lg bg-surface-700 font-mono text-[0.62rem] font-semibold text-accent-300"
      >
        {{ auth.initials }}
      </span>
      <div class="min-w-0 flex-1">
        <strong class="block truncate text-[0.66rem] font-semibold text-content-100">
          {{ auth.displayName }}
        </strong>
        <small class="block text-[0.55rem] text-content-500">
          {{ auth.isSuperAdmin ? 'super admin' : 'admin' }}
        </small>
      </div>
      <button
        type="button"
        class="grid size-8 place-items-center rounded-lg border border-line text-content-400 transition hover:border-signal-error/50 hover:text-signal-error"
        aria-label="Sign out"
        @click="emit('signOut')"
      >
        <LogOut :size="15" />
      </button>
    </div>
  </aside>
</template>
