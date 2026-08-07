<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'

import AppShell from '@/layout/AppShell.vue'

const route = useRoute()
</script>

<template>
  <!-- Login and the 404 render full-bleed; everything else lives in the console shell. -->
  <RouterView v-if="route.meta.bare" />
  <AppShell v-else>
    <RouterView />
  </AppShell>
</template>
