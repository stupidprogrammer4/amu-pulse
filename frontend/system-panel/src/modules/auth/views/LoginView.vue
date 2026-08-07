<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import BrandMark from '@/common/components/BrandMark.vue'
import BrandSparks from '@/common/components/BrandSparks.vue'
import { Eye, EyeOff, LoaderCircle, Lock, ShieldCheck } from '@/common/icons'
import { env } from '@/core/config/env'
import { project } from '@/core/project'
import { useAuthStore } from '@/modules/auth/stores/auth.store'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const username = ref('')
const password = ref('')
const revealed = ref(false)

async function submit(): Promise<void> {
  if (auth.pending) return
  try {
    await auth.login({ username: username.value.trim(), password: password.value })
    const redirect = route.query.redirect
    await router.replace(typeof redirect === 'string' ? redirect : { name: 'overview' })
  } catch {
    // The store already holds the message; the template renders it.
    password.value = ''
  }
}
</script>

<template>
  <div class="grid min-h-screen bg-surface-950 lg:grid-cols-[1.05fr_0.95fr]">
    <!-- Context panel: which backend this panel is about to talk to. -->
    <section
      class="relative hidden flex-col justify-between overflow-hidden border-r border-line bg-surface-900 p-10 lg:flex"
    >
      <!-- The pack's hero banner, pushed off its blue onto the console's gold
           and dimmed under an overlay so the headings stay legible. -->
      <div class="hero-photo pointer-events-none absolute inset-0" />
      <div class="hero-veil pointer-events-none absolute inset-0" />
      <BrandSparks />
      <div
        class="pointer-events-none absolute inset-0"
        style="
          background-image:
            linear-gradient(rgb(255 255 255 / 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgb(255 255 255 / 0.03) 1px, transparent 1px);
          background-size: 46px 46px;
          mask-image: linear-gradient(140deg, black, transparent 78%);
        "
      />
      <div
        class="pointer-events-none absolute -top-40 -left-40 size-[38rem] rounded-full opacity-50"
        style="background: radial-gradient(circle, rgb(212 175 55 / 0.22), transparent 62%)"
      />

      <div class="relative flex items-center gap-3">
        <BrandMark :size="40" />
        <div>
          <strong class="block text-[0.85rem] font-bold tracking-tight text-content-100">
            AMU Pulse
          </strong>
          <small class="block font-mono text-[0.55rem] tracking-[0.16em] text-content-500">
            SYSTEM PANEL
          </small>
        </div>
      </div>

      <div class="relative max-w-xl">
        <span
          class="flex items-center gap-2 font-mono text-[0.58rem] tracking-[0.15em] text-content-400"
        >
          <i class="size-1.5 rounded-full bg-accent-400 shadow-[0_0_10px] shadow-accent-400" />
          OPERATOR ACCESS
        </span>
        <h1 class="mt-6 text-5xl leading-[1.12] font-extrabold tracking-[-0.05em] text-content-100">
          {{ project.tagline }}
        </h1>
        <p class="mt-5 max-w-lg text-[0.78rem] leading-loose text-content-400">
          {{ project.about }}
        </p>
        <p
          class="mt-4 max-w-lg border-l-2 border-accent-500/60 pl-3.5 text-[0.75rem] leading-relaxed text-content-300"
        >
          {{ project.role }}
        </p>
      </div>

      <div class="relative flex gap-10 text-[0.62rem]">
        <div class="flex items-center gap-2.5 text-accent-400">
          <ShieldCheck :size="17" />
          <div>
            <strong class="block text-content-200">Admin guarded</strong>
            <small class="mt-0.5 block font-mono text-[0.53rem] text-content-500">
              /auth/admins/login
            </small>
          </div>
        </div>
        <div class="flex items-center gap-2.5 text-accent-400">
          <Lock :size="17" />
          <div>
            <strong class="block text-content-200">{{ env.environment }}</strong>
            <small class="mt-0.5 block font-mono text-[0.53rem] text-content-500">
              {{ env.apiBaseUrl }}
            </small>
          </div>
        </div>
      </div>
    </section>

    <!-- Form -->
    <section class="grid place-items-center p-6">
      <form class="w-full max-w-sm" novalidate @submit.prevent="submit">
        <BrandMark :size="40" class="lg:hidden" />

        <p class="mt-6 mb-2 text-[0.62rem] font-bold tracking-[0.12em] text-accent-400 lg:mt-0">
          SIGN IN
        </p>
        <h2 class="text-3xl font-extrabold tracking-[-0.05em] text-content-100">Welcome back</h2>
        <p class="mt-2 mb-8 text-[0.72rem] text-content-400">
          Use the administrator credentials issued for this environment.
        </p>

        <label class="mb-5 block">
          <span class="mb-2 block text-[0.66rem] font-semibold text-content-300">Username</span>
          <input
            v-model="username"
            type="text"
            name="username"
            autocomplete="username"
            spellcheck="false"
            required
            class="h-12 w-full rounded-xl border border-line bg-surface-800 px-3.5 text-[0.76rem] text-content-100 outline-none transition placeholder:text-content-500 focus:border-accent-500 focus:ring-3 focus:ring-accent-500/20"
          />
        </label>

        <label class="mb-5 block">
          <span class="mb-2 block text-[0.66rem] font-semibold text-content-300">Password</span>
          <span class="relative block">
            <input
              v-model="password"
              :type="revealed ? 'text' : 'password'"
              name="password"
              autocomplete="current-password"
              required
              class="h-12 w-full rounded-xl border border-line bg-surface-800 pr-11 pl-3.5 text-[0.76rem] text-content-100 outline-none transition focus:border-accent-500 focus:ring-3 focus:ring-accent-500/20"
            />
            <button
              type="button"
              class="absolute inset-y-0 right-3 grid place-items-center text-content-400 hover:text-content-100"
              :aria-label="revealed ? 'Hide password' : 'Show password'"
              @click="revealed = !revealed"
            >
              <EyeOff v-if="revealed" :size="16" />
              <Eye v-else :size="16" />
            </button>
          </span>
        </label>

        <p
          v-if="auth.error"
          class="mb-4 rounded-xl border border-signal-error/35 bg-signal-error/10 px-3.5 py-3 text-[0.68rem] text-signal-error"
        >
          {{ auth.error }}
        </p>

        <button
          type="submit"
          :disabled="auth.pending || !username || !password"
          class="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-accent-500 text-[0.75rem] font-bold text-surface-950 shadow-lg shadow-accent-500/25 transition hover:bg-accent-400 disabled:cursor-not-allowed disabled:opacity-45"
        >
          <LoaderCircle v-if="auth.pending" :size="16" class="animate-spin" />
          {{ auth.pending ? 'Signing in…' : 'Sign in' }}
        </button>

        <p class="mt-6 text-center font-mono text-[0.56rem] text-content-500">
          {{ env.appTitle }} · {{ env.environment }}
        </p>
      </form>
    </section>
  </div>
</template>

<style scoped>
/* The banner ships blue; the filter drags it onto the console's black-and-gold
   before the veil knocks it back far enough to read type over. */
.hero-photo {
  background-image: url('@/assets/brand/hero-2k.webp');
  background-position: center;
  background-size: cover;
  background-repeat: no-repeat;
  filter: grayscale(1) sepia(0.68) saturate(2.2) brightness(0.5) contrast(1.12);
}

.hero-veil {
  background: linear-gradient(
    118deg,
    rgb(8 7 5 / 0.95) 0%,
    rgb(8 7 5 / 0.74) 48%,
    rgb(8 7 5 / 0.46) 100%
  );
}
</style>
