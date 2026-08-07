<script setup lang="ts">
import { useEventListener } from '@vueuse/core'
import { computed, onMounted, ref } from 'vue'

import { CircleAlert, LoaderCircle, RefreshCw, Search, Terminal, X } from '@/common/icons'
import { env } from '@/core/config/env'

import GuardChip from '../components/GuardChip.vue'
import MethodChip from '../components/MethodChip.vue'
import RequestDrawer from '../components/RequestDrawer.vue'
import { useExplorerStore } from '../stores/explorer.store'
import type { Operation } from '../types'

const explorer = useExplorerStore()
const selected = ref<Operation | null>(null)

const contractLabel = computed(() =>
  explorer.document ? `${explorer.document.info.title} · v${explorer.document.info.version}` : '—',
)

onMounted(() => void explorer.load())

// Escape closes the drawer before it closes anything else on the page.
useEventListener(window, 'keydown', (event: KeyboardEvent) => {
  if (event.key === 'Escape' && selected.value) selected.value = null
})
</script>

<template>
  <div>
    <header class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div class="flex items-center gap-3">
        <span class="grid size-11 place-items-center rounded-2xl bg-accent-500/12 text-accent-300">
          <Terminal :size="20" />
        </span>
        <div>
          <span class="font-mono text-[0.58rem] font-semibold tracking-[0.13em] text-accent-400">
            API EXPLORER
          </span>
          <h1 class="mt-1 text-2xl font-extrabold tracking-[-0.045em] text-content-100">
            Every route, callable from here
          </h1>
          <p class="mt-1 text-[0.7rem] text-content-400">
            Read straight from
            <code class="font-mono text-content-300">{{ env.apiBaseUrl }}/openapi.json</code>, so a
            new backend route shows up without a frontend change.
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <div
          class="rounded-xl border border-line bg-surface-800 px-3 py-2 text-right font-mono text-[0.55rem]"
        >
          <small class="block text-content-500">contract</small>
          <strong class="mt-0.5 block text-content-200">{{ contractLabel }}</strong>
        </div>
        <button
          type="button"
          :disabled="explorer.loading"
          class="flex h-11 items-center gap-1.5 rounded-xl border border-line bg-surface-800 px-3.5 text-[0.66rem] text-content-300 transition hover:text-content-100 disabled:opacity-50"
          @click="explorer.load(true)"
        >
          <RefreshCw :size="14" :class="explorer.loading && 'animate-spin'" />
          Reload
        </button>
      </div>
    </header>

    <!-- Toolbar -->
    <div
      class="mb-4 flex flex-wrap items-center gap-2 rounded-2xl border border-line bg-surface-800 p-2.5"
    >
      <label
        class="flex h-9 min-w-56 flex-1 items-center gap-2 rounded-lg border border-line bg-surface-850 px-2.5 text-content-500 focus-within:border-accent-500"
      >
        <Search :size="14" />
        <input
          v-model="explorer.query"
          type="search"
          placeholder="Filter by path, method, tag or summary…"
          spellcheck="false"
          class="min-w-0 flex-1 bg-transparent text-[0.66rem] text-content-100 outline-none placeholder:text-content-500"
        />
      </label>

      <button
        type="button"
        class="flex h-9 items-center gap-1.5 rounded-lg border px-3 font-mono text-[0.58rem] transition"
        :class="
          explorer.panelOnly
            ? 'border-accent-500/40 bg-accent-500/12 text-accent-300'
            : 'border-line bg-surface-850 text-content-400 hover:text-content-100'
        "
        @click="explorer.panelOnly = !explorer.panelOnly"
      >
        /panel only
      </button>

      <button
        v-if="explorer.query || explorer.tag"
        type="button"
        class="flex h-9 items-center gap-1 rounded-lg border border-line bg-surface-850 px-3 text-[0.6rem] text-content-400 transition hover:text-content-100"
        @click="explorer.reset()"
      >
        <X :size="12" />
        Clear
      </button>

      <span class="ml-auto px-1 font-mono text-[0.56rem] text-content-500">
        {{ explorer.stats.shown }} /
        {{ explorer.panelOnly ? explorer.stats.panel : explorer.stats.total }}
        operations
      </span>
    </div>

    <!-- Tags -->
    <div v-if="explorer.tags.length" class="mb-5 flex flex-wrap gap-1.5">
      <button
        type="button"
        class="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[0.6rem] transition"
        :class="
          explorer.tag === null
            ? 'bg-accent-500/12 text-accent-300'
            : 'text-content-400 hover:text-content-100'
        "
        @click="explorer.tag = null"
      >
        All
      </button>
      <button
        v-for="entry in explorer.tags"
        :key="entry.name"
        type="button"
        class="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[0.6rem] transition"
        :class="
          explorer.tag === entry.name
            ? 'bg-accent-500/12 text-accent-300'
            : 'text-content-400 hover:text-content-100'
        "
        @click="explorer.tag = entry.name"
      >
        {{ entry.name }}
        <b class="rounded-full bg-surface-700 px-1.5 font-mono text-[0.5rem] font-normal">
          {{ entry.count }}
        </b>
      </button>
    </div>

    <!-- States -->
    <div
      v-if="explorer.loading && !explorer.document"
      class="grid min-h-64 place-content-center justify-items-center gap-2 text-content-400"
    >
      <LoaderCircle :size="22" class="animate-spin text-accent-400" />
      <p class="text-[0.66rem]">Loading the contract…</p>
    </div>

    <div
      v-else-if="explorer.error"
      class="flex items-start gap-2.5 rounded-2xl border border-signal-error/35 bg-signal-error/10 px-4 py-3.5 text-[0.66rem] text-signal-error"
    >
      <CircleAlert :size="15" class="mt-px shrink-0" />
      <div>
        <p>{{ explorer.error }}</p>
        <button
          type="button"
          class="mt-2 rounded-lg border border-signal-error/40 px-2.5 py-1 text-[0.6rem]"
          @click="explorer.load(true)"
        >
          Try again
        </button>
      </div>
    </div>

    <p
      v-else-if="!explorer.groups.length"
      class="grid min-h-40 place-content-center text-[0.66rem] text-content-500"
    >
      No operation matches that filter.
    </p>

    <!-- Operations -->
    <section v-for="group in explorer.groups" :key="group.tag" class="mb-6">
      <header class="mb-2 flex items-center gap-2">
        <span class="size-1.5 rounded-full bg-accent-400" />
        <h2 class="text-[0.72rem] font-bold text-content-100">{{ group.tag }}</h2>
        <b
          class="rounded-full bg-surface-700 px-1.5 font-mono text-[0.5rem] font-normal text-content-400"
        >
          {{ group.operations.length }}
        </b>
      </header>

      <div class="grid gap-1.5 xl:grid-cols-2">
        <button
          v-for="operation in group.operations"
          :key="operation.id"
          type="button"
          class="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 rounded-xl border border-line bg-surface-800 px-3 py-2.5 text-left transition hover:border-accent-500/40 hover:bg-surface-700"
          @click="selected = operation"
        >
          <MethodChip :method="operation.method" />
          <span class="min-w-0">
            <code class="block truncate font-mono text-[0.65rem] text-content-100">
              {{ operation.path }}
            </code>
            <small class="mt-0.5 block truncate text-[0.56rem] text-content-500">
              {{ operation.summary }}
            </small>
          </span>
          <GuardChip :guard="operation.guard" />
        </button>
      </div>
    </section>

    <RequestDrawer v-if="selected" :operation="selected" @close="selected = null" />
  </div>
</template>
