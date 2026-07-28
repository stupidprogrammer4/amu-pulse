import { defineModule } from '@/core/module'

/** Composes the other modules' pieces into the landing page; owns no data itself. */
export default defineModule({
  name: 'dashboard',
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('./views/DashboardView.vue'),
      meta: { title: 'نبض بازار', nav: { label: 'نبض بازار', order: 10 } },
    },
  ],
})
