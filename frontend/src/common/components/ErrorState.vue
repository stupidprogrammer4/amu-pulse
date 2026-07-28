<script setup lang="ts">
import type { ApiRequestError } from '@/infra/http/api-error'

defineProps<{ error: ApiRequestError }>()
defineEmits<{ retry: [] }>()
</script>

<template>
  <div class="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
    <p class="font-medium">دریافت اطلاعات ناموفق بود</p>
    <p class="mt-1 text-rose-600">{{ error.message }}</p>
    <button
      type="button"
      class="mt-3 rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-rose-700"
      @click="$emit('retry')"
    >
      تلاش دوباره
    </button>
  </div>
</template>
