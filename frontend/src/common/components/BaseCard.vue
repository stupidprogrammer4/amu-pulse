<script setup lang="ts">
defineProps<{
  title?: string
  subtitle?: string
}>()
</script>

<template>
  <section class="card">
    <header v-if="title || $slots.actions" class="mb-4 flex items-start justify-between gap-3">
      <div>
        <h2 v-if="title" class="card-title">{{ title }}</h2>
        <p v-if="subtitle" class="mt-1 text-xs text-slate-400">{{ subtitle }}</p>
      </div>
      <slot name="actions" />
    </header>
    <slot />
  </section>
</template>
