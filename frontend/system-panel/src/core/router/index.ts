import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { env } from '@/core/config/env'
import { setSessionLostHandler } from '@/infra/http'
import { useAuthStore } from '@/modules/auth/stores/auth.store'

declare module 'vue-router' {
  interface RouteMeta {
    /** Reachable without a session — the login screen and the 404. */
    public?: boolean
    /** Rendered outside the console shell. */
    bare?: boolean
    title?: string
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/modules/auth/views/LoginView.vue'),
    meta: { public: true, bare: true, title: 'Sign in' },
  },
  {
    path: '/',
    name: 'overview',
    component: () => import('@/views/OverviewView.vue'),
    meta: { title: 'Overview' },
  },
  {
    path: '/logs',
    name: 'logs',
    component: () => import('@/modules/logs/views/LogsView.vue'),
    meta: { title: 'Logs' },
  },
  {
    path: '/logs/traces/:requestId',
    name: 'log-trace',
    component: () => import('@/modules/logs/views/LogTraceView.vue'),
    meta: { title: 'Trace' },
  },
  {
    path: '/explorer',
    name: 'explorer',
    component: () => import('@/modules/explorer/views/ExplorerView.vue'),
    meta: { title: 'API explorer' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { public: true, bare: true, title: 'Not found' },
  },
]

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  // One /auth/admins/me on the first navigation: a cached token that the
  // backend no longer honours must not get as far as painting the shell.
  const authenticated = await auth.restore()

  if (!to.meta.public && !authenticated) {
    return { name: 'login', query: to.fullPath === '/' ? undefined : { redirect: to.fullPath } }
  }
  if (to.name === 'login' && authenticated) return { name: 'overview' }
  return true
})

router.afterEach((to) => {
  document.title = `${to.meta.title ?? 'Console'} · ${env.appTitle}`
})

// A refresh that fails mid-session drops the operator straight on the login form.
setSessionLostHandler(() => {
  if (router.currentRoute.value.meta.public) return
  void router.replace({ name: 'login', query: { redirect: router.currentRoute.value.fullPath } })
})
