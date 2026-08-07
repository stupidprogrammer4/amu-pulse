<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/modules/auth/stores/auth.store'

import AppSidebar from './AppSidebar.vue'
import AppTopbar from './AppTopbar.vue'

const auth = useAuthStore()
const router = useRouter()
const navOpen = ref(false)

function signOut(): void {
  auth.logout()
  void router.replace({ name: 'login' })
}
</script>

<template>
  <div class="min-h-screen">
    <AppSidebar :open="navOpen" @close="navOpen = false" @sign-out="signOut" />

    <div class="min-h-screen lg:ml-68">
      <AppTopbar @toggle-nav="navOpen = !navOpen" />
      <main class="mx-auto max-w-[100rem] px-4 pt-6 pb-16 sm:px-6 lg:px-8">
        <slot />
      </main>
    </div>
  </div>
</template>
