<script setup lang="ts">
import { LoaderCircle } from '@/common/icons'

withDefaults(defineProps<{ size?: number; label?: string }>(), { size: 18, label: 'Loading' })
</script>

<template>
  <span class="flex items-center gap-2 text-[0.68rem] text-content-400">
    <LoaderCircle :size="size" class="animate-spin text-accent-400" />
    <span>{{ label }}</span>
  </span>
</template>
