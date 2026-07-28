<script setup lang="ts">
withDefaults(defineProps<{ message?: string }>(), { message: 'داده‌ای برای نمایش وجود ندارد.' })
</script>

<template>
  <p class="py-10 text-center text-sm text-slate-400">{{ message }}</p>
</template>
