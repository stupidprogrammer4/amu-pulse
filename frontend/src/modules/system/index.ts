import { defineModule } from '@/core/module'

/** Cross-cutting pages that belong to no feature: 404 today, health/status later. */
export default defineModule({
  name: 'system',
  routes: [
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('./views/NotFoundView.vue'),
      meta: { title: 'صفحه پیدا نشد' },
    },
  ],
})
