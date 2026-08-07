<script setup lang="ts">
import { computed } from 'vue'

import { CircleDot, icons } from '@/common/icons'

const props = withDefaults(defineProps<{ name: string; size?: number }>(), { size: 16 })

// Unknown names fall back to a neutral dot rather than crashing a whole view.
const component = computed(() => icons[props.name] ?? CircleDot)
</script>

<template>
  <component :is="component" :size="props.size" :stroke-width="1.9" />
</template>
