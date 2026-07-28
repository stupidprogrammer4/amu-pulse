import { defineModule } from '@/core/module'

export default defineModule({
  name: 'analysis',
  routes: [
    {
      path: '/analysis',
      name: 'analysis',
      component: () => import('./views/AnalysisView.vue'),
      meta: { title: 'تحلیل بازار', nav: { label: 'تحلیل', order: 30 } },
    },
  ],
})

export { analysisService } from './services/analysis.service'
export { useAnalysisStore } from './stores/analysis.store'
export { default as PulseGauge } from './components/PulseGauge.vue'
export * from './types'
export * from './utils/score'
