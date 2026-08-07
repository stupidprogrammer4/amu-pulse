<script setup lang="ts">
import AppIcon from './AppIcon.vue'

withDefaults(defineProps<{ icon?: string; title: string; body?: string }>(), { icon: 'Search' })
</script>

<template>
  <div class="grid place-items-center px-6 py-14 text-center">
    <span class="grid size-11 place-items-center rounded-xl bg-surface-700 text-content-400">
      <AppIcon :name="icon" :size="19" />
    </span>
    <strong class="mt-3.5 block text-[0.76rem] font-bold text-content-200">{{ title }}</strong>
    <p v-if="body" class="mt-1.5 max-w-sm text-[0.66rem] leading-relaxed text-content-400">
      {{ body }}
    </p>
    <slot />
  </div>
</template>
