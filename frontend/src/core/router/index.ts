import { createRouter, createWebHistory } from 'vue-router'

import { bootRoutes } from '@/core/bootstrap'
import { env } from '@/core/config/env'

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: bootRoutes(),
  scrollBehavior: (_to, _from, savedPosition) => savedPosition ?? { top: 0 },
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} — ${env.appTitle}` : env.appTitle
})

export default router
