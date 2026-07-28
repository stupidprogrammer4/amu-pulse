import { defineModule } from '@/core/module'

export default defineModule({
  name: 'prices',
  routes: [
    {
      path: '/prices',
      name: 'prices',
      component: () => import('./views/PricesView.vue'),
      meta: { title: 'قیمت‌ها', nav: { label: 'قیمت‌ها', order: 20 } },
    },
  ],
})

// Public surface other modules may import.
export { pricesService } from './services/prices.service'
export { usePricesStore } from './stores/prices.store'
export { default as PriceCard } from './components/PriceCard.vue'
export * from './types'
