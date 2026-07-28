<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="py-20 text-center">
    <p class="num text-5xl font-bold text-slate-300">۴۰۴</p>
    <h1 class="mt-4 text-lg font-medium text-slate-700">این صفحه پیدا نشد</h1>
    <RouterLink
      :to="{ name: 'dashboard' }"
      class="mt-6 inline-block rounded-lg bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-700"
    >
      بازگشت به نبض بازار
    </RouterLink>
  </div>
</template>
