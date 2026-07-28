<script setup lang="ts">
withDefaults(defineProps<{ label?: string }>(), { label: 'در حال بارگذاری…' })
</script>

<template>
  <div class="flex items-center justify-center gap-3 py-8 text-sm text-slate-400">
    <span
      class="size-4 animate-spin rounded-full border-2 border-slate-300 border-t-transparent"
      aria-hidden="true"
    />
    <span>{{ label }}</span>
  </div>
</template>
