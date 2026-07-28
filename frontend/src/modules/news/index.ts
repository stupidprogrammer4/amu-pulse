import { defineModule } from '@/core/module'

export default defineModule({
  name: 'news',
  routes: [
    {
      path: '/news',
      name: 'news',
      component: () => import('./views/NewsView.vue'),
      meta: { title: 'اخبار', nav: { label: 'اخبار', order: 40 } },
    },
  ],
})

export { newsService } from './services/news.service'
export { default as NewsList } from './components/NewsList.vue'
export * from './types'
