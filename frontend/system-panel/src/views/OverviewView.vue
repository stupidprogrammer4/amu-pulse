<script setup lang="ts">
import AppIcon from '@/common/components/AppIcon.vue'
import BrandRibbons from '@/common/components/BrandRibbons.vue'
import { env } from '@/core/config/env'
import { navigation } from '@/core/navigation'
import { project } from '@/core/project'
import { useAuthStore } from '@/modules/auth/stores/auth.store'

const auth = useAuthStore()

// Everything the sidebar knows about, flattened — this page doubles as the
// build checklist until each section gets its own view.
const sections = navigation.flatMap((group) =>
  group.items.map((item) => ({ ...item, group: group.title })),
)

const tiles = [
  { label: 'Environment', value: env.environment, icon: 'Activity' },
  { label: 'API base', value: env.apiBaseUrl, icon: 'Terminal' },
  { label: 'Role', value: auth.isSuperAdmin ? 'super admin' : 'admin', icon: 'ShieldCheck' },
  { label: 'Panel sections', value: String(sections.length), icon: 'PanelsTopLeft' },
]
</script>

<template>
  <div>
    <header class="relative mb-6 overflow-hidden rounded-2xl border border-line">
      <BrandRibbons />
      <div
        class="pointer-events-none absolute inset-0"
        style="
          background: linear-gradient(100deg, rgb(8 7 5 / 0.92) 24%, rgb(8 7 5 / 0.35) 100%);
        "
      />
      <div class="relative px-5 py-7 sm:px-7 sm:py-9">
        <span class="font-mono text-[0.58rem] font-semibold tracking-[0.13em] text-accent-400">
          OVERVIEW
        </span>
        <h1 class="mt-2 text-3xl font-extrabold tracking-[-0.045em] text-content-100">
          Signed in as {{ auth.displayName }}
        </h1>
        <p class="mt-2 max-w-xl text-[0.76rem] text-content-400">
          The shell, the session and the API explorer are wired up. Each panel section below lands
          next.
        </p>
      </div>
    </header>

    <!-- What this project is, for anyone opening the console for the first time. -->
    <section class="mb-8 overflow-hidden rounded-2xl border border-line bg-surface-800">
      <div class="grid gap-6 p-5 lg:grid-cols-[1.15fr_0.85fr] lg:p-6">
        <div>
          <span class="font-mono text-[0.55rem] tracking-[0.14em] text-content-500">
            ABOUT THE PROJECT
          </span>
          <h2 class="mt-2 text-xl font-extrabold tracking-[-0.04em] text-content-100">
            {{ project.name }} — {{ project.tagline }}
          </h2>
          <p class="mt-3 text-[0.72rem] leading-relaxed text-content-400">
            {{ project.about }}
          </p>
          <p
            class="mt-4 border-l-2 border-accent-500/60 pl-3.5 text-[0.72rem] leading-relaxed text-content-300"
          >
            {{ project.role }}
          </p>
        </div>

        <ul class="grid content-start gap-2.5">
          <li
            v-for="capability in project.capabilities"
            :key="capability.title"
            class="grid grid-cols-[auto_minmax(0,1fr)] items-start gap-3 rounded-xl border border-line bg-surface-850 p-3.5"
          >
            <span
              class="grid size-8 place-items-center rounded-lg bg-accent-500/12 text-accent-300"
            >
              <AppIcon :name="capability.icon" :size="15" />
            </span>
            <div class="min-w-0">
              <strong class="block text-[0.68rem] font-bold text-content-100">
                {{ capability.title }}
              </strong>
              <p class="mt-1 text-[0.62rem] leading-relaxed text-content-400">
                {{ capability.body }}
              </p>
            </div>
          </li>
        </ul>
      </div>
    </section>

    <div class="mb-8 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <article
        v-for="tile in tiles"
        :key="tile.label"
        class="rounded-2xl border border-line bg-surface-800 p-4"
      >
        <span class="grid size-9 place-items-center rounded-xl bg-accent-500/12 text-accent-300">
          <AppIcon :name="tile.icon" :size="17" />
        </span>
        <small class="mt-3 block text-[0.6rem] text-content-400">{{ tile.label }}</small>
        <strong class="mt-1 block truncate font-mono text-[0.85rem] font-bold text-content-100">
          {{ tile.value }}
        </strong>
      </article>
    </div>

    <section class="overflow-hidden rounded-2xl border border-line bg-surface-800">
      <header class="flex items-center justify-between gap-4 border-b border-line px-4 py-3.5">
        <div>
          <h2 class="text-[0.78rem] font-bold text-content-100">Panel surface</h2>
          <p class="mt-0.5 text-[0.6rem] text-content-400">
            Every guarded route group the console will drive.
          </p>
        </div>
      </header>

      <div
        v-for="item in sections"
        :key="item.label"
        class="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 border-b border-line/70 px-4 py-3 last:border-0"
      >
        <span class="grid size-8 place-items-center rounded-lg bg-surface-700 text-content-400">
          <AppIcon :name="item.icon" :size="15" />
        </span>
        <div class="min-w-0">
          <strong class="block text-[0.7rem] font-semibold text-content-200">
            {{ item.label }}
          </strong>
          <small class="block truncate font-mono text-[0.56rem] text-content-500">
            {{ item.endpoint ?? '—' }}
          </small>
        </div>
        <span
          class="rounded-full px-2 py-0.5 font-mono text-[0.52rem] font-semibold"
          :class="
            item.ready ? 'bg-accent-500/14 text-accent-300' : 'bg-surface-700 text-content-500'
          "
        >
          {{ item.ready ? 'ready' : 'pending' }}
        </span>
      </div>
    </section>
  </div>
</template>
